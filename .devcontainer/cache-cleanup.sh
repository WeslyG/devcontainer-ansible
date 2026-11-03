#!/bin/sh
# Preserve the normal Docker RUN shell and its exit status.
/bin/sh "$@"
command_status=$?
if [ "$command_status" -ne 0 ]; then
    exit "$command_status"
fi

set -eu
if [ "$(id -u)" -eq 0 ]; then
    apt-get clean
    rm -rf /var/lib/apt/lists/*
    rm -f /var/cache/apt/*.bin
    for cache_home in /root /home/*; do
        [ -d "$cache_home" ] || continue
        rm -rf -- "$cache_home/.cache/pip" "$cache_home/.npm"
    done
    rm -rf /usr/local/share/nvm/.cache /tmp/tmp-k9s
else
    cache_home="$(getent passwd "$(id -u)" | cut -d: -f6)"
    if [ -n "$cache_home" ]; then
        rm -rf -- "$cache_home/.cache/pip" "$cache_home/.npm"
    fi
fi
