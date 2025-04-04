#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""This script adds fingerprints to the deleted_keys table in the Hockeypuck's database."""


import argparse
import logging
import os
from typing import List

import psycopg2

logger = logging.getLogger(__name__)


class KeyBlockError(Exception):
    """Exception raised for errors in the key blocking operation."""


def _get_db_connection() -> psycopg2.extensions.connection:
    """Connect to the Postgres database.

    Returns:
        psycopg2.extensions.connection: the database connection.

    Raises:
        KeyBlockError: if the connection fails.
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
        raise KeyBlockError(f"Failed to connect to database: {e}") from e


def _insert_fingerprints_to_table(
    cursor: psycopg2.extensions.cursor, fingerprints: List[str], comment: str
) -> None:
    """Add fingerprints to the deleted_keys table.

    Args:
        cursor: the database cursor.
        fingerprints: list of fingerprints to block.
        comment: the comment associated with blocking.

    Raises:
        KeyBlockError: if any SQL command fails.
    """
    logging.info("Blocking fingerprints: %s", ", ".join(fingerprints))
    try:
        insert_args = ",".join(
            cursor.mogrify("(LOWER(%s), %s)", (fingerprint, comment)).decode("utf-8")
            for fingerprint in fingerprints
        )
        query = (
            "INSERT INTO deleted_keys (fingerprint, comment) VALUES "
            f"{insert_args} ON CONFLICT DO NOTHING;"
        )
        cursor.execute(query)
        logging.info("Block process completed successfully.")
    except psycopg2.Error as e:
        raise KeyBlockError(f"Error executing SQL commands: {e}") from e


def main() -> None:
    """Block list of fingerprints.

    Raises:
        KeyBlockError: if the key blocking operation fails.
    """
    parser = argparse.ArgumentParser(description="Block keys in the Hockeypuck Postgres database.")
    parser.add_argument(
        "--fingerprints", required=True, help="Comma-separated list of fingerprints to block"
    )
    parser.add_argument("--comment", required=True, help="Comment associated with the blocking")
    args = parser.parse_args()
    fingerprints = args.fingerprints.split(",")
    comment = args.comment
    try:
        with _get_db_connection() as conn:
            with conn.cursor() as cursor:
                _insert_fingerprints_to_table(cursor, fingerprints, comment)
    except KeyBlockError as e:
        logging.error("Unable to block keys: %s", e)
        raise KeyBlockError(f"Unable to block keys: {e}") from e


if __name__ == "__main__":  # pragma: no cover
    main()
