#!/bin/bash

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

TEMPLATE_FILE="/hockeypuck/etc/hockeypuck.conf.tmpl"
OUTPUT_FILE="/hockeypuck/etc/hockeypuck.conf"

if [[ ! -f $TEMPLATE_FILE ]]; then
    echo "Template file $TEMPLATE_FILE not found." >&2
    exit 1
fi

envsubst < "$TEMP_FILE" > "$OUTPUT_FILE"

echo "Substitution complete. Output written to $OUTPUT_FILE."

exec /hockeypuck/bin/hockeypuck -config $OUTPUT_FILE
