#!/bin/sh
set -eu
ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
BIN="$ROOT_DIR/secuagentos-audit"
STATE_DIR=$(mktemp -d)
trap 'rm -rf "$STATE_DIR"' EXIT
export SECUAGENTOS_STATE_DIR="$STATE_DIR"
$BIN record foundation foundation_boot success 'stage=FOUNDATION_READY'
$BIN status | grep -q 'status=READY'
grep -q 'actor=foundation' "$STATE_DIR/audit/audit.log"
grep -q 'action=foundation_boot' "$STATE_DIR/audit/audit.log"
echo 'Audit Manager smoke test: PASS'
