#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

import argparse
import logging
import os

import psycopg2

logger = logging.getLogger(__name__)


def get_db_connection():
    """Connect to the Postgres database."""
    db_password = os.getenv("POSTGRESQL_DB_PASSWORD")
    db_name = os.getenv("POSTGRESQL_DB_NAME")
    db_host = os.getenv("POSTGRESQL_DB_HOSTNAME")
    db_user = os.getenv("POSTGRESQL_DB_USERNAME")
    dsn = f"dbname={db_name} user={db_user} password={db_password} host={db_host}"
    try:
        conn = psycopg2.connect(dsn)
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        exit(1)


def delete_fingerprints(cursor, fingerprints, comment):
    """Delete fingerprints from the database.
    Args:
        cursor: the database cursor.
        fingerprints: list of fingerprints to delete.
        comment: the comment associated with the deletion."""
    logging.info(f"Deleting fingerprints: {', '.join(fingerprints)}")
    try:
        for fp in fingerprints:
            cursor.execute(
                """
                INSERT INTO deleted_keys (fingerprint, comment)
                VALUES (LOWER(%s), %s)
                ON CONFLICT DO NOTHING;
            """,
                (fp, comment),
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
        print("Deletion process completed successfully.")
    except Exception as e:
        print(f"Error executing SQL commands: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Delete keys from the Hockeypuck Postgres database by fingerprint."
    )
    parser.add_argument(
        "--fingerprints", required=True, help="Comma-separated list of fingerprints to delete"
    )
    parser.add_argument("--comment", required=True, help="Comment associated with the deletion")
    args = parser.parse_args()
    fingerprints = args.fingerprints.split(",")
    comment = args.comment

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        delete_fingerprints(cursor, fingerprints, comment)
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":  # pragma: no cover
    main()
