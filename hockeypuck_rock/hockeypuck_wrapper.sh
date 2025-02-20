#!/bin/bash

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

# Retrieve blacklisted keys from the Hockeypuck postgres database and start the hockeypuck binary

set -euo pipefail

export PGPASSWORD=${POSTGRESQL_DB_PASSWORD}

SQLCMD="psql -t -A -d ${POSTGRESQL_DB_NAME} -h ${POSTGRESQL_DB_HOSTNAME} -U ${POSTGRESQL_DB_USERNAME}"

BLACKLIST_FINGERPRINTS=$($SQLCMD -c "SELECT STRING_AGG(fingerprint, ',') FROM deleted_keys;")

export APP_BLACKLIST_FINGERPRINTS="$BLACKLIST_FINGERPRINTS"

/hockeypuck/bin/hockeypuck -config /hockeypuck/etc/hockeypuck.conf
