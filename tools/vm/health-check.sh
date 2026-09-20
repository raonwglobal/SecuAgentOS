#!/bin/sh
set -eu

STATE_DIR="${SECUAGENTOS_STATE_DIR:-/run/secuagentos}"
HEALTH_FILE="$STATE_DIR/health"
EXPECTED="${1:-READY}"

[ -r "$HEALTH_FILE" ] || { echo "health file not found: $HEALTH_FILE" >&2; exit 1; }
grep -qx "status=$EXPECTED" "$HEALTH_FILE" || { echo "unexpected health status" >&2; cat "$HEALTH_FILE" >&2; exit 1; }
grep -qx "state=SYSTEM_READY" "$HEALTH_FILE" || { echo "SYSTEM_READY not reached" >&2; cat "$HEALTH_FILE" >&2; exit 1; }
echo "SecuAgentOS health: $EXPECTED"
