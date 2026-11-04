#!/usr/bin/env bash
set -euo pipefail
feature_dir="${FEATURE_DIR:-/feature}"
work_dir="$(mktemp -d)"
trap 'rm -rf -- "$work_dir"' EXIT
before="$(sha256sum /usr/local/bin/node)"
if VERSION=latest bash "$feature_dir/install.sh" > "$work_dir/version.log" 2>&1; then
    echo 'ERROR: accepted a floating Node version' >&2; exit 1
fi
grep -q 'exact release version' "$work_dir/version.log"
mkdir "$work_dir/bin"
cat > "$work_dir/bin/apt-get" <<'SH'
#!/bin/sh
exit 0
SH
cat > "$work_dir/bin/curl" <<'SH'
#!/bin/sh
set -eu
while [ "$#" -gt 0 ]; do
    if [ "$1" = -o ]; then printf 'corrupted archive' > "$2"; exit 0; fi
    shift
done
exit 1
SH
chmod +x "$work_dir/bin/apt-get" "$work_dir/bin/curl"
zero="$(printf '%064d' 0)"
if PATH="$work_dir/bin:$PATH" VERSION=24.22.2 NPMVERSION=12.2.1 SHA256AMD64="$zero" SHA256ARM64="$zero" \
    bash "$feature_dir/install.sh" > "$work_dir/checksum.log" 2>&1; then
    echo 'ERROR: accepted a corrupted Node archive' >&2; exit 1
fi
grep -q 'did NOT match' "$work_dir/checksum.log"
test "$(sha256sum /usr/local/bin/node)" = "$before"
echo 'PASS: Node feature rejects floating versions and corruption without replacing installed Node'
