#!/usr/bin/env bash
set -euo pipefail
apt-get update
apt-get install -y --no-install-recommends libfido2-dev libcbor-dev
curl -fsSL --retry 2 --connect-timeout 15 --max-time 120 "https://cdn.openbsd.org/pub/OpenBSD/OpenSSH/portable/openssh-${OPENSSH_VERSION:?}.tar.gz" -o /tmp/openssh.tar.gz
echo "${OPENSSH_SHA256:?}  /tmp/openssh.tar.gz" | sha256sum --check
mkdir /tmp/openssh
tar -xzf /tmp/openssh.tar.gz -C /tmp/openssh --strip-components=1
cd /tmp/openssh
CFLAGS=-O2 LDFLAGS=-Wl,-s ./configure --prefix=/usr/local --sysconfdir=/etc/ssh \
    --with-kerberos5 --with-libedit --with-security-key-builtin
make -j"$(nproc)"
mkdir -p /ssh-runtime/usr/local/bin /ssh-runtime/usr/local/libexec \
    /ssh-runtime/usr/local/share/licenses/openssh /ssh-runtime/etc/ssh/ssh_config.d /ssh-runtime/DEBIAN
for binary in ssh scp sftp ssh-add ssh-agent ssh-keygen ssh-keyscan; do
    install -m 0755 "$binary" "/ssh-runtime/usr/local/bin/$binary"
done
for binary in ssh-keysign ssh-pkcs11-helper ssh-sk-helper; do
    install -m 0755 "$binary" "/ssh-runtime/usr/local/libexec/$binary"
done
install -m 0644 ssh_config /ssh-runtime/etc/ssh/ssh_config
cp LICENCE /ssh-runtime/usr/local/share/licenses/openssh/
printf 'Package: openssh-client\nSource: openssh\nVersion: 1:%s\nArchitecture: %s\nMaintainer: Ansible infra maintainers\nDepends: libc6, libssl3t64, zlib1g, libedit2, libfido2-1, libcbor0.10, libgssapi-krb5-2, libkrb5-3\nDescription: OpenSSH clients built from checksum-pinned upstream source\n' "$OPENSSH_VERSION" "$(dpkg --print-architecture)" > /ssh-runtime/DEBIAN/control
echo /etc/ssh/ssh_config > /ssh-runtime/DEBIAN/conffiles
dpkg-deb --build --root-owner-group /ssh-runtime /openssh-client.deb
