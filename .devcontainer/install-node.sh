#!/usr/bin/env bash
set -euo pipefail

version="${NODE_VERSION:?Set the exact Node.js release version}"
if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "NODE_VERSION must be an exact release version." >&2
    exit 1
fi
case "$(dpkg --print-architecture)" in
    amd64) architecture=x64; checksum="${NODE_SHA256_AMD64:?Missing amd64 checksum}" ;;
    arm64) architecture=arm64; checksum="${NODE_SHA256_ARM64:?Missing arm64 checksum}" ;;
    *) echo "Node.js installation supports amd64 and arm64 only." >&2; exit 1 ;;
esac
if [[ ! "$checksum" =~ ^[a-f0-9]{64}$ ]]; then
    echo "Expected a SHA256 checksum for the Node.js release archive." >&2
    exit 1
fi
work_dir="$(mktemp -d)"
trap 'rm -rf -- "$work_dir"' EXIT
archive="node-v${version}-linux-${architecture}.tar.xz"
curl --fail --silent --show-error --location --retry 3 --connect-timeout 15 --max-time 180 \
    "https://nodejs.org/dist/v${version}/${archive}" -o "$work_dir/$archive"
printf '%s  %s\n' "$checksum" "$work_dir/$archive" | sha256sum --check -
tar -xJf "$work_dir/$archive" -C /usr/local --strip-components=1 --no-same-owner

# Keep only the requested Node.js/npm/npx toolchain.
rm -rf /usr/local/lib/node_modules/corepack
rm -f /usr/local/bin/corepack /usr/local/bin/pnpm /usr/local/bin/pnpx \
    /usr/local/bin/yarn /usr/local/bin/yarnpkg
node --version
npm --version
