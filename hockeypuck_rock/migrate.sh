#!/bin/bash

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

set -euo pipefail

export PGPASSWORD="${POSTGRESQL_DB_PASSWORD}" 
SQLCMD="psql ${POSTGRESQL_DB_NAME} -h ${POSTGRESQL_DB_HOSTNAME} -U ${POSTGRESQL_DB_USERNAME}"
$SQLCMD -c "CREATE TABLE IF NOT EXISTS deleted_keys (fingerprint TEXT PRIMARY KEY NOT NULL, comment TEXT NOT NULL);"
