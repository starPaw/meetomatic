#!/bin/sh
set -eu
if [ "${RENEWED_LINEAGE:-}" = "/etc/letsencrypt/live/meet.example.com" ]; then
    /bin/systemctl reload nginx
fi
