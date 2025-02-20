#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Delete keys from the Hockeypuck Postgres database by fingerprint."""

import argparse
import logging
import os
import re
import sys
from typing import List

import psycopg2

logger = logging.getLogger(__name__)


def get_db_connection() -> psycopg2.extensions.connection | None:
    """Connect to the Postgres database.

    Returns:
        psycopg2.extensions.connection: the database connection.
    """
    db_password = os.getenv("POSTGRESQL_DB_PASSWORD")
    db_name = os.getenv("POSTGRESQL_DB_NAME")
    db_host = os.getenv("POSTGRESQL_DB_HOSTNAME")
    db_user = os.getenv("POSTGRESQL_DB_USERNAME")
    dsn = f"dbname={db_name} user={db_user} password={db_password} host={db_host}"
    try:
        conn = psycopg2.connect(dsn)
        conn.autocommit = True
        return conn
    except psycopg2.OperationalError as e:
        logging.error("Failed to connect to database: %s", e)
        return None


def delete_fingerprints(
    cursor: psycopg2.extensions.cursor, fingerprints: List[str], comment: str
) -> None:
    """Delete fingerprints from the database.

    Args:
        cursor: the database cursor.
        fingerprints: list of fingerprints to delete.
        comment: the comment associated with the deletion.
    """
    logging.info("Deleting fingerprints: %s", ", ".join(fingerprints))
    try:
        for fingerprint in fingerprints:
            cursor.execute(
                """
                INSERT INTO deleted_keys (fingerprint, comment)
                VALUES (LOWER(%s), %s)
                ON CONFLICT DO NOTHING;
            """,
                (fingerprint, comment),
            )

        cursor.execute(
            """
            DELETE FROM subkeys USING deleted_keys
            WHERE subkeys.rfingerprint = REVERSE(deleted_keys.fingerprint);
        """
        )
        cursor.execute("ALTER TABLE subkeys DROP CONSTRAINT IF EXISTS subkeys_rfingerprint_fkey;")
        cursor.execute(
            """
            DELETE FROM keys USING deleted_keys
            WHERE keys.rfingerprint = REVERSE(deleted_keys.fingerprint);
        """
        )
        cursor.execute(
            """
            ALTER TABLE subkeys
            ADD CONSTRAINT subkeys_rfingerprint_fkey
            FOREIGN KEY (rfingerprint)
            REFERENCES keys(rfingerprint);
            """
        )
        logging.info("Deletion process completed successfully.")
    except psycopg2.Error as e:
        logging.error("Error executing SQL commands: %s", e)


def main() -> None:
    """Main entrypoint."""
    parser = argparse.ArgumentParser(
        description="Delete keys from the Hockeypuck Postgres database by fingerprint."
    )
    parser.add_argument(
        "--fingerprints", required=True, help="Comma-separated list of fingerprints to delete"
    )
    parser.add_argument("--comment", required=True, help="Comment associated with the deletion")
    args = parser.parse_args()
    fingerprints = args.fingerprints.split(",")
    for fingerprint in fingerprints:
        # fingperints are usually of length 40 or 64 depending on the hash algorithm, and
        # consist of hexadecimal characters only.
        if not re.fullmatch(r"[0-9A-Fa-f]{40}|[0-9A-Fa-f]{64}", fingerprint):
            logging.error("Invalid fingerprint format: %s", fingerprint)
            sys.exit(1)

    comment = args.comment

    conn = get_db_connection()
    if conn is None:
        sys.exit(1)
    cursor = conn.cursor()
    try:
        delete_fingerprints(cursor, fingerprints, comment)
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":  # pragma: no cover
    main()
