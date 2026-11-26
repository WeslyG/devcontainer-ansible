#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
    echo 'CLI tools feature must be installed as root.' >&2; exit 1
fi
claude_version="${CLAUDEVERSION:?Set an exact Claude Code version}"
elasticdump_version="${ELASTICDUMPVERSION:?Set an exact elasticdump version}"
ip_address_version="${IPADDRESSVERSION:?Set exact ip-address security override}"
form_data_version="${FORMDATA2VERSION:?Set exact compatible form-data 2.x security override}"
for version in "$claude_version" "$elasticdump_version" "$ip_address_version" "$form_data_version"; do
    if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo 'Specify exact release versions for Claude Code and elasticdump.' >&2; exit 1
    fi
done
case "$(dpkg --print-architecture)" in
    amd64) architecture=x64; integrity="${CLAUDEINTEGRITYAMD64:?Set native package SHA512 integrity}" ;;
    arm64) architecture=arm64; integrity="${CLAUDEINTEGRITYARM64:?Set native package SHA512 integrity}" ;;
    *) echo 'Native Claude supports amd64/arm64 here.' >&2; exit 1 ;;
esac
remote_user="${_REMOTE_USER:-vscode}"
remote_home="$(getent passwd "$remote_user" | cut -d: -f6)"
test -n "$remote_home"
work_dir="$(mktemp -d)"
trap 'rm -rf -- "$work_dir"' EXIT
package="claude-code-linux-${architecture}"
curl --fail --silent --show-error --location --retry 3 --connect-timeout 15 --max-time 240 \
    "https://registry.npmjs.org/@anthropic-ai/${package}/-/${package}-${claude_version}.tgz?ansible-infra=${RANDOM}${RANDOM}" -o "$work_dir/native.tgz"
python - "$work_dir/native.tgz" "$integrity" <<'PY'
import base64,hashlib,sys
from pathlib import Path
expected=sys.argv[2]
assert expected.startswith('sha512-'), 'Expected a SHA512 npm integrity value'
actual='sha512-'+base64.b64encode(hashlib.sha512(Path(sys.argv[1]).read_bytes()).digest()).decode()
if actual!=expected:raise SystemExit('Native Claude archive integrity mismatch')
print('PASS: native Claude npm archive SHA512')
PY
mkdir "$work_dir/unpacked"
tar -xzf "$work_dir/native.tgz" -C "$work_dir/unpacked" --no-same-owner
# The official platform npm package contains the same standalone native CLI.
# Only one executable is kept in the user's native layout; no npm wrapper copy.
binary="$(find "$work_dir/unpacked/package" -type f \( -name claude -o -name claude.exe \) -print)"
if [ -z "$binary" ] || [[ "$binary" = *$'\n'* ]]; then
    echo 'Expected exactly one native Claude binary in the official package.' >&2; exit 1
fi
runuser -u "$remote_user" -- mkdir -p \
    "$remote_home/.local/share/claude/versions" "$remote_home/.local/bin"
install -m 0755 -o "$remote_user" -g "$(id -gn "$remote_user")" \
    "$binary" "$remote_home/.local/share/claude/versions/$claude_version"
runuser -u "$remote_user" -- ln -sfn "$remote_home/.local/share/claude/versions/$claude_version" "$remote_home/.local/bin/claude"
ln -sfn "$remote_home/.local/bin/claude" /usr/local/bin/claude
claude --version
# An application package owns its explicit transitive security overrides.
application=/usr/local/share/elasticdump
mkdir -p "$application"
node - "$application/package.json" "$elasticdump_version" "$ip_address_version" "$form_data_version" <<'JS'
const fs=require('node:fs');
fs.writeFileSync(process.argv[2], JSON.stringify({name:'ansible-infra-elasticdump',version:'1.0.0',private:true,
  dependencies:{elasticdump:process.argv[3]},overrides:{'ip-address':process.argv[4],'form-data@<3':process.argv[5]}},null,2)+'\n');
JS
npm install --prefix "$application" --omit=dev --no-audit --no-fund
ln -sfn "$application/node_modules/.bin/elasticdump" /usr/local/bin/elasticdump
ln -sfn "$application/node_modules/.bin/multielasticdump" /usr/local/bin/multielasticdump
npm cache clean --force
elasticdump --version
