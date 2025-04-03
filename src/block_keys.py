#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""This script adds fingerprints to the deleted_keys table in the Hockeypuck's database."""


import logging
import re
from typing import List

import psycopg2

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR)


class InvalidFingerprintError(Exception):
    """Exception raised for invalid fingerprint format."""

    def __init__(self, fingerprints: List[str]) -> None:
        """Initialize the exception.

        Args:
            fingerprints: list of invalid fingerprints.
        """
        self.fingerprints = fingerprints
        self.message = f"Invalid fingerprints: {', '.join(fingerprints)}"
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return the exception message.

        Returns:
            str: the exception message.
        """
        return (
            f"{self.message}. Fingerprints must be 40 or 64 characters long and "
            "consist of hexadecimal characters only."
        )


class KeyBlockError(Exception):
    """Exception raised for errors in the key blocking operation."""


def _get_db_connection(db_credentials: dict[str, str] | None) -> psycopg2.extensions.connection:
    """Connect to the Postgres database.

    Returns:
        psycopg2.extensions.connection: the database connection.

    Raises:
        KeyBlockError: if the connection fails.
    """
    if db_credentials is None:
        raise KeyBlockError("Database credentials unavailable.")
    db_password = db_credentials["db-password"]
    db_name = db_credentials["db-name"]
    db_host = db_credentials["db-hostname"]
    db_user = db_credentials["db-username"]
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


def check_valid_fingerprints(fingerprints: list) -> None:
    """Check if fingerprints are valid.

    Args:
        fingerprints: List of fingerprints to validate

    Raises:
        InvalidFingerprintError: if any of the fingerprints are invalid.
    """
    invalid_fingerprints = []
    for fingerprint in fingerprints:
        # fingerprints are usually of length 40 or 64 depending on the hash algorithm, and
        # consist of hexadecimal characters only.
        if not re.fullmatch(r"[0-9A-Fa-f]{40}|[0-9A-Fa-f]{64}", fingerprint):
            logging.error("Invalid fingerprint format: %s", fingerprint)
            invalid_fingerprints.append(fingerprint)
    if invalid_fingerprints:
        raise InvalidFingerprintError(invalid_fingerprints)


def block_keys(fingerprints: list, comment: str, db_credentials: dict[str, str] | None) -> None:
    """Block list of fingerprints.

    Args:
        fingerprints: List of fingerprints to block.
        comment: the comment associated with blocking.
        db_credentials: Hockeypuck database credentials.

    Raises:
        KeyBlockError: if the key blocking operation fails.
    """
    try:
        with _get_db_connection(db_credentials) as conn:
            with conn.cursor() as cursor:
                _insert_fingerprints_to_table(cursor, fingerprints, comment)
    except KeyBlockError as e:
        logging.error("Unable to block keys: %s", e)
        raise KeyBlockError(f"Unable to block keys: {e}") from e
