#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
BIN="$ROOT_DIR/secuagentos-foundation"
STATE_DIR=$(mktemp -d)
trap 'rm -rf "$STATE_DIR"' EXIT

export SECUAGENTOS_STATE_DIR="$STATE_DIR"

version="$($BIN version)"
[ "$version" = 'SecuAgentOS Foundation v0.1.0' ]

printf '%s\n' 'SYSTEM_READY' > "$STATE_DIR/state"
printf '%s\n' 'status=READY' > "$STATE_DIR/health"

$BIN status | grep -q 'state=SYSTEM_READY'
$BIN health | grep -q 'status=READY'

echo 'Foundation smoke test: PASS'
