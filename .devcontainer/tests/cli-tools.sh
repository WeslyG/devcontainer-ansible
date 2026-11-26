#!/usr/bin/env bash
set -euo pipefail
feature_dir="${FEATURE_DIR:-/feature}"
work_dir="$(mktemp -d)"
trap 'rm -rf -- "$work_dir"' EXIT
before="$(sha256sum /usr/local/bin/claude)"
mkdir "$work_dir/bin"
cat > "$work_dir/bin/curl" <<'SH'
#!/bin/sh
set -eu
while [ "$#" -gt 0 ]; do
    if [ "$1" = -o ]; then printf 'corrupted native archive' > "$2"; exit 0; fi
    shift
done
exit 1
SH
chmod +x "$work_dir/bin/curl"
if PATH="$work_dir/bin:$PATH" CLAUDEVERSION=2.1.318 ELASTICDUMPVERSION=6.125.1 IPADDRESSVERSION=10.7.5 FORMDATA2VERSION=2.5.6 \
    CLAUDEINTEGRITYAMD64=sha512-invalid CLAUDEINTEGRITYARM64=sha512-invalid \
    bash "$feature_dir/install.sh" > "$work_dir/corrupt.log" 2>&1; then
    echo 'ERROR: accepted a corrupted native Claude package' >&2; exit 1
fi
grep -q 'integrity mismatch' "$work_dir/corrupt.log"
test "$(sha256sum /usr/local/bin/claude)" = "$before"
echo 'PASS: native Claude rejects package corruption without replacing the installed binary'
