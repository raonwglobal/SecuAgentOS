#!/bin/sh
set -eu
ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
BIN="$ROOT_DIR/secuagentos-event-bus"
STATE_DIR=$(mktemp -d)
trap 'rm -rf "$STATE_DIR"' EXIT
export SECUAGENTOS_STATE_DIR="$STATE_DIR"

id="$($BIN emit foundation.test '{"state":"READY"}')"
[ -n "$id" ]
grep -q 'type=foundation.test' "$STATE_DIR/events/events.log"
grep -q 'payload={"state":"READY"}' "$STATE_DIR/events/events.log"
$BIN health | grep -q 'status=READY'
echo 'Event Bus smoke test: PASS'
