#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
INIT="$ROOT_DIR/system/init/secuagentos-init"

for command in sh grep; do command -v "$command" >/dev/null 2>&1 || exit 1; done
[ -x "$INIT" ] || { echo "init is not executable" >&2; exit 1; }

TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

# Static lifecycle contract check. Full VM execution is performed by CI/host runners.
SECUAGENTOS_STATE_DIR="$TMP_DIR/state"
mkdir -p "$SECUAGENTOS_STATE_DIR"

# Validate required state names and VM tooling prerequisites without starting a nested VM here.
for state in FOUNDATION_READY SECURITY_READY SERVICES_READY RUNTIME_READY SYSTEM_READY; do
  grep -q "transition $state" "$INIT" || { echo "missing state: $state" >&2; exit 1; }
done

grep -q 'SECUAGENTOS_HEALTH=READY' "$INIT"
grep -q 'secuagentos.fail=' "$INIT"

echo "SecuAgentOS VM smoke contract: PASS"
