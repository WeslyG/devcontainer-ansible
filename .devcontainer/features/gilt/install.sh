#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
    echo "Gilt feature must be installed as root." >&2
    exit 1
fi

version="${VERSION:-2.2.5}"
version="${version#v}"
if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Specify an exact Gilt release version, for example 2.2.5." >&2
    exit 1
fi

if [ "$(uname -s)" != "Linux" ]; then
    echo "Gilt feature supports Linux only." >&2
    exit 1
fi
case "$(uname -m)" in
    x86_64 | amd64) architecture="amd64" ;;
    aarch64 | arm64) architecture="arm64" ;;
    *) echo "Unsupported Gilt architecture: $(uname -m)" >&2; exit 1 ;;
esac

if ! command -v curl >/dev/null || [ ! -s /etc/ssl/certs/ca-certificates.crt ]; then
    if ! command -v apt-get >/dev/null; then
        echo "Install curl and ca-certificates before using the Gilt feature." >&2
        exit 1
    fi
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends curl ca-certificates
fi

work_dir="$(mktemp -d)"
trap 'rm -rf -- "$work_dir"' EXIT
asset="gilt_${version}_linux_${architecture}"
release_url="https://github.com/retr0h/gilt/releases/download/v${version}"

curl --fail --silent --show-error --location --retry 3 --connect-timeout 15 --max-time 180 \
    --output "$work_dir/$asset" "$release_url/$asset"
curl --fail --silent --show-error --location --retry 3 --connect-timeout 15 --max-time 180 \
    --output "$work_dir/checksums.txt" "$release_url/checksums.txt"

awk -v asset="$asset" '$2 == asset || $2 == "*" asset { print }' \
    "$work_dir/checksums.txt" > "$work_dir/selected-checksum.txt"
if [ "$(wc -l < "$work_dir/selected-checksum.txt")" -ne 1 ]; then
    echo "Expected exactly one checksum for $asset in the release manifest." >&2
    exit 1
fi
(
    cd "$work_dir"
    sha256sum --check selected-checksum.txt
)

install -m 0755 "$work_dir/$asset" /usr/local/bin/gilt
gilt version
