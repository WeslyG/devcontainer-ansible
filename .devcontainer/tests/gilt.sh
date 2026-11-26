#!/usr/bin/env bash
set -euo pipefail

feature_dir="${FEATURE_DIR:-/feature}"
# Load build options from the mounted feature metadata.
eval "$(python - "$feature_dir/devcontainer-feature.json" <<'PY'
import json,shlex,sys
for key,item in json.load(open(sys.argv[1]))['options'].items():
 if key!='version':print('export '+key.upper()+'='+shlex.quote(item['default']))
PY
)"
export GILT_VERSION="${GILT_VERSION:-2.2.5}"
gilt version | python -c 'import json,sys,os; data=json.load(sys.stdin); assert data["gitVersion"] == os.environ["GILT_VERSION"]; assert data["goVersion"] == "go"+os.environ["GOVERSION"]'
original_checksum="$(sha256sum /usr/local/bin/gilt)"

work_dir="$(mktemp -d)"
trap 'rm -rf -- "$work_dir"' EXIT
bash "$(dirname "${BASH_SOURCE[0]}")/gilt-overlay.sh"
mkdir "$work_dir/bin"
cat > "$work_dir/bin/curl" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
while [ "$#" -gt 0 ]; do
    case "$1" in
        --output) output="$2"; shift 2 ;;
        *) url="$1"; shift ;;
    esac
done
case "$(uname -m)" in
    x86_64) architecture=amd64 ;;
    aarch64) architecture=arm64 ;;
esac
case "$url" in
    */checksums.txt)
        asset="gilt_${GILT_VERSION}_linux_${architecture}"
        if [ "${TEST_MISSING_CHECKSUM:-0}" = 1 ]; then asset=another-binary; fi
        printf '%064d  %s\n' 0 "$asset" > "$output"
        ;;
    *) printf 'corrupted release binary\n' > "$output" ;;
esac
SH
chmod +x "$work_dir/bin/curl"

if PATH="$work_dir/bin:$PATH" SOURCESHA256="$(printf %064d 0)" VERSION="$GILT_VERSION" bash "$feature_dir/install.sh" > "$work_dir/corrupt.log" 2>&1; then
    echo "ERROR: accepted a corrupted release binary" >&2
    exit 1
fi
grep -q 'did NOT match' "$work_dir/corrupt.log"
test "$(sha256sum /usr/local/bin/gilt)" = "$original_checksum"
echo "PASS: rejects a corrupted source archive without replacing the installed Gilt"

if VERSION=latest bash "$feature_dir/install.sh" > "$work_dir/version.log" 2>&1; then
    echo "ERROR: accepted an unpinned version" >&2
    exit 1
fi
grep -q 'Specify an exact Gilt release version' "$work_dir/version.log"
echo "PASS: requires a pinned release version"

test "$(ec --version)" = "v$EDITORCONFIGVERSION"
test "$(readlink -f /usr/local/bin/ec)" = "$(readlink -f /usr/local/bin/editorconfig-checker)"
