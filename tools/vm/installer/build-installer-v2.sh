#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
OUT_DIR="$ROOT_DIR/.build/vm/installer-v2"
WORK_DIR="$OUT_DIR/work"
SEED_DIR="$WORK_DIR/nocloud"
mkdir -p "$SEED_DIR"

BASE_ISO_URL="${UBUNTU_INSTALLER_ISO_URL:-https://releases.ubuntu.com/24.04/ubuntu-24.04.3-live-server-amd64.iso}"
BASE_ISO="$WORK_DIR/ubuntu-live-server-amd64.iso"
OUTPUT="$OUT_DIR/secuagentos-x86_64-installer-v2.iso"
USER_DATA="$SEED_DIR/user-data"
META_DATA="$SEED_DIR/meta-data"
GRUB_CFG="$WORK_DIR/grub.cfg"
EFI_GRUB_CFG="$WORK_DIR/efi-grub.cfg"

need() { command -v "$1" >/dev/null 2>&1 || { echo "missing required command: $1" >&2; exit 1; }; }
need curl
need sha256sum
need xorriso
need python3

# Require a deployment-specific SHA-512 crypt hash; never bake in a default password.
if [ -z "${SECUAGENTOS_PASSWORD_HASH:-}" ]; then
  echo "SECUAGENTOS_PASSWORD_HASH is required (SHA-512 crypt hash from a secure source)" >&2
  exit 2
fi
SECUAGENTOS_PASSWORD_HASH="$SECUAGENTOS_PASSWORD_HASH" python3 - <<'PY'
import os, re, sys
value = os.environ["SECUAGENTOS_PASSWORD_HASH"]
if not re.fullmatch(r"\$6\$[A-Za-z0-9./]{1,16}\$[A-Za-z0-9./]{80,}", value):
    sys.exit("SECUAGENTOS_PASSWORD_HASH must be a valid SHA-512 crypt hash")
PY

curl -fsSL --retry 3 --retry-delay 2 "$BASE_ISO_URL" -o "$BASE_ISO"
cp "$ROOT_DIR/tools/vm/installer/autoinstall/user-data" "$USER_DATA"
cat > "$META_DATA" <<'EOF'
instance-id: secuagentos-installer-v2
local-hostname: secuagentos
EOF

# Inject only the caller-provided password hash into the installer seed.
SECUAGENTOS_PASSWORD_HASH="$SECUAGENTOS_PASSWORD_HASH" USER_DATA="$USER_DATA" python3 - <<'PY'
import os
from pathlib import Path
p = Path(os.environ["USER_DATA"])
text = p.read_text()
old = '    password: "$6$rounds=4096$SecuAgentOS$REPLACE_AT_INSTALL_TIME"'
new = '    password: "' + os.environ["SECUAGENTOS_PASSWORD_HASH"] + '"'
if old not in text:
    raise SystemExit("expected password placeholder not found in autoinstall user-data")
p.write_text(text.replace(old, new, 1))
PY

# Extract both GRUB menus, then add NoCloud autoinstall arguments to Linux entries.
xorriso -osirrox on -indev "$BASE_ISO" -extract /boot/grub/grub.cfg "$GRUB_CFG"
test -s "$GRUB_CFG" || { echo "Ubuntu ISO missing /boot/grub/grub.cfg" >&2; exit 1; }
if xorriso -osirrox on -indev "$BASE_ISO" -extract /EFI/BOOT/grub.cfg "$EFI_GRUB_CFG" >/dev/null 2>&1; then
  test -s "$EFI_GRUB_CFG" || rm -f "$EFI_GRUB_CFG"
fi

GRUB_CFG="$GRUB_CFG" EFI_GRUB_CFG="$EFI_GRUB_CFG" python3 - <<'PY'
import os, re
from pathlib import Path
args = r"autoinstall ds=nocloud\;s=/cdrom/nocloud/"
paths = [Path(os.environ["GRUB_CFG"]), Path(os.environ["EFI_GRUB_CFG"])]
patched = 0
for path in paths:
    if not path.is_file() or not path.stat().st_size:
        continue
    lines = path.read_text(errors="replace").splitlines()
    output = []
    for line in lines:
        if re.match(r"^\s*linux(?:efi)?\s", line) and "autoinstall" not in line:
            if re.search(r"\s---(?:\s|$)", line):
                line = re.sub(r"\s---(?=\s|$)", " " + args + " ---", line, count=1)
            else:
                line += " " + args
            patched += 1
        output.append(line)
    # xorriso may restore ISO files read-only; make the extracted menu writable before patching.
    path.chmod(path.stat().st_mode | 0o200)
    path.write_text("\n".join(output) + "\n")
if patched == 0:
    raise SystemExit("no GRUB Linux boot entries were patched; refusing to emit non-autoinstall ISO")
PY

# Replay original BIOS/UEFI boot metadata while adding the NoCloud seed and patched menus.
rm -f "$OUTPUT"
set -- -indev "$BASE_ISO" -outdev "$OUTPUT" -boot_image any replay
set -- "$@" -map "$USER_DATA" /nocloud/user-data -map "$META_DATA" /nocloud/meta-data
set -- "$@" -map "$GRUB_CFG" /boot/grub/grub.cfg
if [ -s "$EFI_GRUB_CFG" ]; then
  set -- "$@" -map "$EFI_GRUB_CFG" /EFI/BOOT/grub.cfg
fi
set -- "$@" -commit -end
xorriso "$@"

test -s "$OUTPUT"
sha256sum "$OUTPUT" > "$OUTPUT.sha256"
sha256sum -c "$OUTPUT.sha256"

cat > "$OUT_DIR/BUILD-MANIFEST.txt" <<EOF
SecuAgentOS Installer v2
Base ISO: Ubuntu Server 24.04
Architecture: amd64
Boot media: $OUTPUT
NoCloud seed: /nocloud/user-data and /nocloud/meta-data embedded in installer ISO
Autoinstall: enabled in GRUB boot entries
Credential handling: password hash supplied at build time; not stored in repository
Foundation boundary: /opt/secuagentos
Service Manager boundary: systemd
EOF

echo "Built: $OUTPUT"
