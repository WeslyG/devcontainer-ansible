#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
    echo "CLI tools feature must be installed as root." >&2
    exit 1
fi
claude_version="${CLAUDEVERSION:-2.1.317}"
elasticdump_version="${ELASTICDUMPVERSION:-6.125.1}"
for version in "$claude_version" "$elasticdump_version"; do
    if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "Specify exact release versions for Claude Code and elasticdump." >&2
        exit 1
    fi
done
remote_user="${_REMOTE_USER:-vscode}"
remote_home="$(getent passwd "$remote_user" | cut -d: -f6)"
if [ -z "$remote_home" ]; then
    echo "Remote user $remote_user must exist before installing CLI tools." >&2
    exit 1
fi

work_dir="$(mktemp -d)"
chmod 0755 "$work_dir"
trap 'rm -rf -- "$work_dir"' EXIT
curl --fail --silent --show-error --location --retry 3 --connect-timeout 15 --max-time 180 \
    https://storage.googleapis.com/claude-code-dist-86c565f3-f756-42ad-8dfa-d59b1c096819/claude-code-releases/bootstrap.sh -o "$work_dir/install-claude.sh"
chmod 0644 "$work_dir/install-claude.sh"
runuser -u "$remote_user" -- env HOME="$remote_home" \
    bash "$work_dir/install-claude.sh" "$claude_version"

# Preserve the native user-owned launcher and its automatic updates.
# A global symlink replaces the upstream feature's second full binary copy.
ln -sfn "$remote_home/.local/bin/claude" /usr/local/bin/claude
claude --version
npm install --global --omit=dev "elasticdump@$elasticdump_version"
npm cache clean --force
elasticdump --version
