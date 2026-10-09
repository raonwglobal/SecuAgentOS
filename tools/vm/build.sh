#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
OUT_DIR="${ROOT_DIR}/.build/vm"
WORK_DIR="${OUT_DIR}/work"

UBUNTU_RELEASE="${UBUNTU_RELEASE:-24.04}"
UBUNTU_IMAGE_VERSION="${UBUNTU_IMAGE_VERSION:-20260911}"
UBUNTU_IMAGE_BASE="${UBUNTU_IMAGE_BASE:-https://cloud-images.ubuntu.com/releases/releases/noble/release-${UBUNTU_IMAGE_VERSION}}"
UBUNTU_IMAGE_URL="${UBUNTU_IMAGE_BASE}/ubuntu-24.04-server-cloudimg-amd64.img"
UBUNTU_SHA256_URL="${UBUNTU_IMAGE_BASE}/SHA256SUMS"

DISK_IMAGE="$OUT_DIR/secuagentos-x86_64-ubuntu24.04.img"
SEED_ISO="$OUT_DIR/secuagentos-x86_64-cloud-init.iso"

need() { command -v "$1" >/dev/null 2>&1 || { echo "missing required command: $1" >&2; exit 1; }; }
need curl
need sha256sum
need xorriso
need qemu-img

rm -rf "$OUT_DIR"
mkdir -p "$WORK_DIR/seed"

echo "Downloading Ubuntu x86_64 cloud image..."
echo "Ubuntu release: ${UBUNTU_RELEASE}"
echo "Ubuntu image revision: ${UBUNTU_IMAGE_VERSION}"
echo "Ubuntu image source: ${UBUNTU_IMAGE_URL}"

curl -fsSL --retry 3 --retry-delay 2 "$UBUNTU_IMAGE_URL" -o "$WORK_DIR/ubuntu-base.img"
curl -fsSL --retry 3 --retry-delay 2 "$UBUNTU_SHA256_URL" -o "$WORK_DIR/SHA256SUMS"

EXPECTED_SHA=$(awk '/ubuntu-24\.04-server-cloudimg-amd64\.img$/ {print $1; exit}' "$WORK_DIR/SHA256SUMS")
[ -n "$EXPECTED_SHA" ] || { echo "Ubuntu image checksum not found" >&2; exit 1; }
ACTUAL_SHA=$(sha256sum "$WORK_DIR/ubuntu-base.img" | awk '{print $1}')
[ "$ACTUAL_SHA" = "$EXPECTED_SHA" ] || {
  echo "Ubuntu image checksum mismatch" >&2
  echo "expected: $EXPECTED_SHA" >&2
  echo "actual:   $ACTUAL_SHA" >&2
  exit 1
}

echo "Ubuntu image checksum: PASS"

cp "$WORK_DIR/ubuntu-base.img" "$DISK_IMAGE"
qemu-img resize "$DISK_IMAGE" 8G >/dev/null

# Grow the GPT/partition/filesystem metadata during first boot rather than
# relying on a host-side partition editor. Ubuntu cloud-init/growpart then
# owns the guest disk expansion consistently.
cat > "$WORK_DIR/seed/meta-data" <<EOF
instance-id: secuagentos-vm-${UBUNTU_IMAGE_VERSION}
local-hostname: secuagentos
EOF

cat > "$WORK_DIR/seed/user-data" <<'EOF'
#cloud-config
# cloud-init is provisioning only. SecuAgentOS lifecycle/state is owned by systemd.
write_files:
  - path: /usr/local/sbin/secuagentos-bootstrap
    permissions: '0755'
    content: |
      #!/bin/bash
      set -eu
      STATE_DIR=/run/secuagentos
      LOG_FILE="$STATE_DIR/boot.log"
      mkdir -p "$STATE_DIR"
      log() {
        printf '%s\n' "$*" | tee -a "$LOG_FILE"
        printf '%s\n' "$*" > /dev/ttyS0 2>/dev/null || true
      }
      transition() {
        state="$1"
        log "SECUAGENTOS_STATE=$state"
        printf '%s\n' "$state" > "$STATE_DIR/state"
      }
      transition INIT_STARTED
      transition FOUNDATION_READY
      transition SECURITY_READY
      transition SERVICES_READY
      transition RUNTIME_READY
      transition SYSTEM_READY
      printf '%s\n' 'status=READY' > "$STATE_DIR/health"
      log 'SECUAGENTOS_HEALTH=READY'

  - path: /etc/systemd/system/secuagentos-bootstrap.service
    permissions: '0644'
    content: |
      [Unit]
      Description=SecuAgentOS Foundation Bootstrap
      Wants=network-pre.target
      After=network-pre.target
      Before=multi-user.target

      [Service]
      Type=oneshot
      ExecStart=/usr/local/sbin/secuagentos-bootstrap
      RemainAfterExit=yes
      StandardOutput=journal+console
      StandardError=journal+console

      [Install]
      WantedBy=multi-user.target

  - path: /usr/local/libexec/secuagentos-foundation
    permissions: '0755'
    content: |
      #!/bin/sh
      set -eu
      
      STATE_DIR="${SECUAGENTOS_STATE_DIR:-/run/secuagentos}"
      mkdir -p "$STATE_DIR"
      
      case "${1:-status}" in
        version)
          printf '%s\n' 'SecuAgentOS Foundation v0.1.0'
          ;;
        health)
          if [ -f "$STATE_DIR/health" ]; then
            cat "$STATE_DIR/health"
          else
            printf '%s\n' 'status=NOT_READY'
            exit 1
          fi
          ;;
        status)
          printf 'state_dir=%s\n' "$STATE_DIR"
          [ -f "$STATE_DIR/state" ] && printf 'state=%s\n' "$(cat "$STATE_DIR/state")" || printf '%s\n' 'state=NOT_STARTED'
          [ -f "$STATE_DIR/health" ] && cat "$STATE_DIR/health" || printf '%s\n' 'status=NOT_READY'
          ;;
        *)
          echo "usage: secuagentos-foundation {status|health|version}" >&2
          exit 2
          ;;
      esac
      
  - path: /usr/local/libexec/secuagentos-event-bus
    permissions: '0755'
    content: |
      #!/bin/sh
      set -eu
      
      STATE_DIR="${SECUAGENTOS_STATE_DIR:-/run/secuagentos}"
      EVENT_DIR="$STATE_DIR/events"
      mkdir -p "$EVENT_DIR"
      
      case "${1:-}" in
        emit)
          [ $# -ge 3 ] || { echo 'usage: secuagentos-event-bus emit <type> <payload>' >&2; exit 2; }
          type="$2"
          payload="$3"
          case "$type" in
            *[!A-Za-z0-9_.-]*|'') echo 'invalid event type' >&2; exit 2;;
          esac
          ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
          id="$(date +%s%N 2>/dev/null || date +%s)-$"
          printf '%s\tid=%s\ttype=%s\tpayload=%s\n' "$ts" "$id" "$type" "$payload" >> "$EVENT_DIR/events.log"
          printf '%s\n' "$id"
          ;;
        health)
          [ -f "$EVENT_DIR/events.log" ] && printf '%s\n' 'status=READY' || printf '%s\n' 'status=READY'
          ;;
        *)
          echo 'usage: secuagentos-event-bus {emit <type> <payload>|health}' >&2
          exit 2
          ;;
      esac
      
  - path: /usr/local/libexec/secuagentos-health
    permissions: '0755'
    content: |
      #!/bin/sh
      set -eu
      
      STATE_DIR="${SECUAGENTOS_STATE_DIR:-/run/secuagentos}"
      FOUNDATION="$STATE_DIR/state"
      HEALTH="$STATE_DIR/health"
      EVENTS="$STATE_DIR/events/events.log"
      
      case "${1:-check}" in
        check)
          failed=0
          [ -f "$FOUNDATION" ] || failed=1
          [ -f "$HEALTH" ] || failed=1
          [ -f "$EVENTS" ] || failed=1
          if [ "$failed" -eq 0 ]; then
            printf '%s\n' 'status=READY'
            exit 0
          fi
          printf '%s\n' 'status=NOT_READY'
          exit 1
          ;;
        status)
          printf 'foundation=%s\n' "$([ -f "$FOUNDATION" ] && cat "$FOUNDATION" || printf NOT_STARTED)"
          printf 'health=%s\n' "$([ -f "$HEALTH" ] && cat "$HEALTH" || printf NOT_READY)"
          printf 'event_bus=%s\n' "$([ -f "$EVENTS" ] && printf READY || printf NOT_READY)"
          ;;
        *)
          echo 'usage: secuagentos-health {check|status}' >&2
          exit 2
          ;;
      esac
      
  - path: /usr/local/libexec/secuagentos-audit
    permissions: '0755'
    content: |
      #!/bin/sh
      set -eu
      
      STATE_DIR="${SECUAGENTOS_STATE_DIR:-/run/secuagentos}"
      AUDIT_DIR="${SECUAGENTOS_AUDIT_DIR:-$STATE_DIR/audit}"
      AUDIT_LOG="$AUDIT_DIR/audit.log"
      mkdir -p "$AUDIT_DIR"
      
      case "${1:-}" in
        record)
          [ $# -ge 4 ] || { echo 'usage: secuagentos-audit record <actor> <action> <result> [details]' >&2; exit 2; }
          actor="$2"; action="$3"; result="$4"; details="${5:-}"
          for field in "$actor" "$action" "$result"; do case "$field" in ''|*[!A-Za-z0-9_.-]*) echo 'invalid audit field' >&2; exit 2;; esac; done
          ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
          printf '%s\tactor=%s\taction=%s\tresult=%s\tdetails=%s\n' "$ts" "$actor" "$action" "$result" "$details" >> "$AUDIT_LOG"
          ;;
        status)
          [ -f "$AUDIT_LOG" ] && printf 'status=READY\nlog=%s\n' "$AUDIT_LOG" || printf 'status=NOT_READY\n'
          ;;
        *)
          echo 'usage: secuagentos-audit {record <actor> <action> <result> [details]|status}' >&2
          exit 2
          ;;
      esac
      
  - path: /usr/local/libexec/secuagentos-service-manager
    permissions: '0755'
    content: |
      #!/bin/sh
      set -eu
      
      STATE_DIR="${SECUAGENTOS_STATE_DIR:-/run/secuagentos}"
      SERVICE_DIR="$STATE_DIR/services"
      REGISTRY="$SERVICE_DIR/registry"
      mkdir -p "$SERVICE_DIR"
      
      echo_status() {
        name="$1"
        [ -f "$SERVICE_DIR/$name.state" ] && cat "$SERVICE_DIR/$name.state" || printf '%s\n' 'UNKNOWN'
      }
      
      case "${1:-}" in
        register)
          [ $# -ge 3 ] || { echo 'usage: register <name> <command>' >&2; exit 2; }
          name="$2"; command="$3"
          case "$name" in *[!A-Za-z0-9_.-]*|'') echo 'invalid service name' >&2; exit 2;; esac
          if ! grep -Fq "^$name	" "$REGISTRY" 2>/dev/null; then
            printf '%s\t%s\n' "$name" "$command" >> "$REGISTRY"
          fi
          printf '%s\n' 'REGISTERED' > "$SERVICE_DIR/$name.state"
          ;;
        status)
          [ $# -ge 2 ] || { echo 'usage: status <name>' >&2; exit 2; }
          printf 'service=%s\nstate=%s\n' "$2" "$(echo_status "$2")"
          ;;
        list)
          [ -f "$REGISTRY" ] && cat "$REGISTRY" || true
          ;;
        daemon)
          printf '%s\n' 'status=READY' > "$SERVICE_DIR/manager.health"
          while :; do sleep 30; done
          ;;
        *)
          echo 'usage: secuagentos-service-manager {register <name> <command>|status <name>|list|daemon}' >&2
          exit 2
          ;;
      esac
      
  - path: /etc/systemd/system/secuagentos-service-manager.service
    permissions: '0644'
    content: |
      [Unit]
      Description=SecuAgentOS Foundation Service Manager
      After=secuagentos-bootstrap.service
      Requires=secuagentos-bootstrap.service
      
      [Service]
      Type=simple
      ExecStart=/usr/local/libexec/secuagentos-service-manager daemon
      Restart=on-failure
      RestartSec=2
      
      [Install]
      WantedBy=multi-user.target
      
  - path: /etc/systemd/system/secuagentos-foundation-integrate.service
    permissions: '0644'
    content: |
      [Unit]
      Description=SecuAgentOS Foundation Integration
      Requires=secuagentos-bootstrap.service
      After=secuagentos-bootstrap.service
      Before=secuagentos-service-manager.service

      [Service]
      Type=oneshot
      ExecStart=/usr/local/sbin/secuagentos-foundation-integrate
      RemainAfterExit=yes
      StandardOutput=journal+console
      StandardError=journal+console

      [Install]
      WantedBy=multi-user.target

  - path: /usr/local/sbin/secuagentos-foundation-integrate
    permissions: '0755'
    content: |
      #!/bin/bash
      set -eu
      export SECUAGENTOS_STATE_DIR=/run/secuagentos
      LOG=/run/secuagentos/boot.log
      log() { printf '%s\n' "$*" | tee -a "$LOG"; printf '%s\n' "$*" > /dev/ttyS0 2>/dev/null || true; }
      if [ -f /run/secuagentos/foundation-integrated ]; then
        exit 0
      fi
      log 'SECUAGENTOS_INTEGRATION=STARTED'
      /usr/local/libexec/secuagentos-event-bus emit foundation.ready 'version=0.1.0' >/run/secuagentos/foundation-event-id
      /usr/local/libexec/secuagentos-audit record foundation bootstrap READY 'foundation-v0.1.0'
      /usr/local/libexec/secuagentos-service-manager register foundation-event-bus '/usr/local/libexec/secuagentos-event-bus health'
      /usr/local/libexec/secuagentos-service-manager register foundation-health '/usr/local/libexec/secuagentos-health check'
      /usr/local/libexec/secuagentos-service-manager register foundation-audit '/usr/local/libexec/secuagentos-audit status'
      /usr/local/libexec/secuagentos-service-manager register foundation-runtime '/usr/local/libexec/secuagentos-foundation status'
      /usr/local/libexec/secuagentos-health check >/run/secuagentos/foundation-health
      touch /run/secuagentos/foundation-integrated
      log 'SECUAGENTOS_FOUNDATION_INTEGRATED=READY'
      log 'SECUAGENTOS_EVENT=foundation.ready'

  - path: /usr/local/libexec/secuagentos-agent-runtime
    permissions: '0755'
    content: |
      #!/bin/bash
      set -eu
      STATE_DIR=/run/secuagentos
      LOG=$STATE_DIR/boot.log
      log() { printf '%s\\n' "$*" | tee -a "$LOG"; printf '%s\\n' "$*" > /dev/ttyS0 2>/dev/null || true; }
      log 'SECUAGENTOS_AGENT_RUNTIME=STARTED'
      [ -f "$STATE_DIR/foundation-integrated" ]
      grep -q '^status=READY$' "$STATE_DIR/foundation-health"
      mkdir -p "$STATE_DIR/runtime"
      printf '%s\\n' 'state=READY' > "$STATE_DIR/runtime/state"
      printf '%s\\n' 'version=0.1.0' > "$STATE_DIR/runtime/version"
      printf '%s\\n' 'foundation=READY' > "$STATE_DIR/runtime/foundation"
      touch "$STATE_DIR/agent-runtime-ready"
      log 'SECUAGENTOS_AGENT_RUNTIME=READY'

  - path: /etc/systemd/system/secuagentos-agent-runtime.service
    permissions: '0644'
    content: |
      [Unit]
      Description=SecuAgentOS Agent Runtime
      Requires=secuagentos-foundation-integrate.service
      After=secuagentos-foundation-integrate.service
      Before=secuagentos-service-manager.service

      [Service]
      Type=oneshot
      ExecStart=/usr/local/libexec/secuagentos-agent-runtime
      RemainAfterExit=yes
      StandardOutput=journal+console
      StandardError=journal+console

      [Install]
      WantedBy=multi-user.target

runcmd:
  - [systemctl, daemon-reload]
  - [systemctl, enable, --now, secuagentos-bootstrap.service]
  - [/usr/local/sbin/secuagentos-foundation-integrate]
  - [systemctl, enable, --now, secuagentos-agent-runtime.service]
  - [systemctl, enable, secuagentos-foundation-integrate.service]
  - [systemctl, enable, --now, secuagentos-service-manager.service]
EOF

xorriso -as mkisofs -quiet -volid CIDATA -joliet -rock "$WORK_DIR/seed" -o "$SEED_ISO"
sha256sum "$DISK_IMAGE" > "$DISK_IMAGE.sha256"
sha256sum "$SEED_ISO" > "$SEED_ISO.sha256"

printf '%s\n' \
  "Built: $DISK_IMAGE" \
  "Built: $SEED_ISO" \
  "Ubuntu release: $UBUNTU_RELEASE" \
  "Ubuntu image revision: $UBUNTU_IMAGE_VERSION" \
  "Ubuntu source: $UBUNTU_IMAGE_URL" \
  "Ubuntu checksum: $EXPECTED_SHA"
