#!/bin/sh
set -eu
ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
BIN="$ROOT_DIR/secuagentos-health"
STATE_DIR=$(mktemp -d)
trap 'rm -rf "$STATE_DIR"' EXIT
export SECUAGENTOS_STATE_DIR="$STATE_DIR"
mkdir -p "$STATE_DIR/events"
printf '%s\n' SYSTEM_READY > "$STATE_DIR/state"
printf '%s\n' status=READY > "$STATE_DIR/health"
printf '%s\n' 'event' > "$STATE_DIR/events/events.log"
$BIN check | grep -q 'status=READY'
$BIN status | grep -q 'event_bus=READY'
echo 'Health Manager smoke test: PASS'
