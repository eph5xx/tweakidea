#!/usr/bin/env bash
# test_install_uv.sh — verify bin/install.js hard-fails when uv is missing.
#
# Exit codes: 0 = test passed; 1 = test failed; 77 = test skipped.
# UV-01 per schemas/version.json schema.

set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
INSTALL_JS="$ROOT/bin/install.js"

if [ ! -f "$INSTALL_JS" ]; then
  echo "SKIP: $INSTALL_JS not found"
  exit 77
fi

# Strip uv from PATH by excluding any directory containing a uv binary.
SCRUBBED_PATH=""
IFS=':' read -ra PARTS <<< "$PATH"
for dir in "${PARTS[@]}"; do
  if [ -n "$dir" ] && [ ! -x "$dir/uv" ]; then
    SCRUBBED_PATH="${SCRUBBED_PATH:+$SCRUBBED_PATH:}$dir"
  fi
done

# Ensure node is still reachable
if ! PATH="$SCRUBBED_PATH" command -v node > /dev/null 2>&1; then
  echo "SKIP: node not in scrubbed PATH — cannot run test"
  exit 77
fi

# Sanity: ensure uv is NOT in scrubbed PATH
if PATH="$SCRUBBED_PATH" command -v uv > /dev/null 2>&1; then
  echo "SKIP: unable to scrub uv from PATH — test cannot run"
  exit 77
fi

# Run installer in a temp cwd so it doesn't clobber anything
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

PATH="$SCRUBBED_PATH" node "$INSTALL_JS" --local > "$WORK/stdout.log" 2> "$WORK/stderr.log"
EXIT_CODE=$?

if [ "$EXIT_CODE" -eq 0 ]; then
  echo "FAIL: install.js exited 0 with no uv on PATH (expected non-zero)"
  cat "$WORK/stderr.log"
  exit 1
fi

if ! grep -q "requires 'uv'" "$WORK/stderr.log"; then
  echo "FAIL: stderr did not contain \"requires 'uv'\" remediation message"
  cat "$WORK/stderr.log"
  exit 1
fi

if ! grep -q "curl -LsSf https://astral.sh/uv/install.sh" "$WORK/stderr.log"; then
  echo "FAIL: stderr did not contain the curl install hint"
  cat "$WORK/stderr.log"
  exit 1
fi

echo "PASS: install.js hard-fails on missing uv with correct remediation message"
exit 0
