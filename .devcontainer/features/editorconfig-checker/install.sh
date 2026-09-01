#!/bin/sh

set -eu

VERSION="${VERSION:-3.11.1}"
VERSION="${VERSION#v}"

case "$(uname -s)" in
    Linux) os="linux" ;;
    *)
        echo "Unsupported operating system: $(uname -s)" >&2
        exit 1
        ;;
esac

case "$(uname -m)" in
    x86_64 | amd64) architecture="amd64" ;;
    aarch64 | arm64) architecture="arm64" ;;
    i386 | i486 | i586 | i686) architecture="386" ;;
    armv7l | armv7) architecture="armv7" ;;
    armv6l | armv6) architecture="armv6" ;;
    *)
        echo "Unsupported architecture: $(uname -m)" >&2
        exit 1
        ;;
esac

for command_name in curl tar install sha256sum; do
    if ! command -v "${command_name}" >/dev/null 2>&1; then
        echo "Required command is not installed: ${command_name}" >&2
        exit 1
    fi
done

archive_name="editorconfig-checker-${os}-${architecture}.tar.gz"
download_url="https://github.com/editorconfig-checker/editorconfig-checker/releases/download/v${VERSION}/${archive_name}"
checksums_url="https://github.com/editorconfig-checker/editorconfig-checker/releases/download/v${VERSION}/checksums.txt"
temporary_directory="$(mktemp -d)"

cleanup() {
    rm -rf "${temporary_directory}"
}
trap cleanup EXIT INT TERM

echo "Installing editorconfig-checker ${VERSION} for ${os}/${architecture}..."
curl --fail --location --retry 3 --output "${temporary_directory}/${archive_name}" "${download_url}"
curl --fail --location --retry 3 --output "${temporary_directory}/checksums.txt" "${checksums_url}"
(
    cd "${temporary_directory}"
    grep "  ${archive_name}$" checksums.txt | sha256sum --check --strict -
)
tar -xzf "${temporary_directory}/${archive_name}" -C "${temporary_directory}"
install -m 0755 "${temporary_directory}/editorconfig-checker" /usr/local/bin/editorconfig-checker

editorconfig-checker --version
