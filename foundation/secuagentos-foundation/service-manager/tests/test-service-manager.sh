#!/bin/sh
set -eu
ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
BIN="$ROOT_DIR/secuagentos-service-manager"
STATE_DIR=$(mktemp -d)
trap 'rm -rf "$STATE_DIR"' EXIT
export SECUAGENTOS_STATE_DIR="$STATE_DIR"

$BIN register test-agent '/opt/test-agent/run'
$BIN status test-agent | grep -q 'state=REGISTERED'
$BIN list | grep -q 'test-agent'
echo 'Service Manager smoke test: PASS'
