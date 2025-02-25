#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""This script deletes keys from Hockeypuck by fingerprint.

The script performs the following actions:

1. Deleting the keys and subkeys corresponding to the fingerprint from the Postgres database.
2. Delete all the files in /hockeypuck/data/ptree directory to remove the key from leveldb.
3. Invoke the hockeypuck-pbuild binary to rebuild the prefix tree.
"""

import argparse
import logging
import os
import re
import shutil
from typing import List

import psycopg2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PTREE_DATA_DIR = "/hockeypuck/data/ptree"


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


class KeyDeletionError(Exception):
    """Exception raised for errors in the key deletion operation."""


class PtreeDataError(Exception):
    """Exception raised for errors in the ptree data deletion operations."""


class DatabaseConnectionError(Exception):
    """Exception raised for errors in the database connection."""


class DatabaseOperationError(Exception):
    """Exception raised for errors in the database operations."""


class PrefixTreeRebuildError(Exception):
    """Exception raised for errors in the prefix tree rebuild operation."""


def remove_ptree_data() -> None:
    """Remove all data from the ptree directory.

    Raises:
        PtreeDataError: if the ptree data directory does not exist or deletion fails.
    """
    if not os.path.exists(PTREE_DATA_DIR):
        raise PtreeDataError(f"Ptree data directory does not exist: {PTREE_DATA_DIR}")
    for filename in os.listdir(PTREE_DATA_DIR):
        file_path = os.path.join(PTREE_DATA_DIR, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except OSError as e:
            raise PtreeDataError(f"Failed to delete {file_path}: {e}") from e


def invoke_rebuild_prefix_tree() -> None:
    """Invoke the prefix_tree_rebuild binary.

    Raises:
        PrefixTreeRebuildError: if the rebuild operation fails.
    """
    command = " ".join(
        [
            "/hockeypuck/bin/hockeypuck-pbuild",
            "-config",
            "/hockeypuck/etc/hockeypuck.conf",
        ]
    )
    result = os.system(command)
    if result != 0:
        logging.error("Failed to invoke prefix_tree_rebuild, return code: %d", result)
        raise PrefixTreeRebuildError(f"prefix_tree_rebuild failed with return code: {result}")
    logging.info("prefix_tree_rebuild invoked successfully.")


def get_db_connection() -> psycopg2.extensions.connection:
    """Connect to the Postgres database.

    Returns:
        psycopg2.extensions.connection: the database connection.

    Raises:
        DatabaseConnectionError: if the connection fails.
    """
    db_password = os.getenv("POSTGRESQL_DB_PASSWORD")
    db_name = os.getenv("POSTGRESQL_DB_NAME")
    db_host = os.getenv("POSTGRESQL_DB_HOSTNAME")
    db_user = os.getenv("POSTGRESQL_DB_USERNAME")
    dsn = f"dbname={db_name} user={db_user} password={db_password} host={db_host}"
    try:
        conn = psycopg2.connect(dsn)
        return conn
    except psycopg2.OperationalError as e:
        raise DatabaseConnectionError(f"Failed to connect to database: {e}") from e


def delete_fingerprints(
    cursor: psycopg2.extensions.cursor, fingerprints: List[str], comment: str
) -> None:
    """Delete fingerprints from the database.

    Args:
        cursor: the database cursor.
        fingerprints: list of fingerprints to delete.
        comment: the comment associated with the deletion.

    Raises:
        DatabaseOperationError: if any SQL command fails.
    """
    logging.info("Deleting fingerprints: %s", ", ".join(fingerprints))
    try:
        cursor.execute("BEGIN;")

        insert_args = ",".join(
            cursor.mogrify("(LOWER(%s), %s)", (fingerprint, comment)).decode("utf-8")
            for fingerprint in fingerprints
        )
        query = (
            "INSERT INTO deleted_keys (fingerprint, comment) VALUES "
            f"{insert_args} ON CONFLICT DO NOTHING;"
        )
        cursor.execute(query)

        cursor.execute("SET CONSTRAINTS ALL DEFERRED;")

        cursor.execute(
            """
            DELETE FROM subkeys USING deleted_keys
            WHERE subkeys.rfingerprint = REVERSE(deleted_keys.fingerprint);
        """
        )

        cursor.execute(
            """
            DELETE FROM keys USING deleted_keys
            WHERE keys.rfingerprint = REVERSE(deleted_keys.fingerprint);
        """
        )

        cursor.connection.commit()

        logging.info("Deletion process completed successfully.")
    except psycopg2.Error as e:
        raise DatabaseOperationError(f"Error executing SQL commands: {e}") from e


def main() -> None:
    """Main entrypoint.

    Raises:
        InvalidFingerprintError: if any of the fingerprints are invalid.
        KeyDeletionError: if any of the operations fail.
    """
    parser = argparse.ArgumentParser(
        description="Delete keys from the Hockeypuck Postgres database by fingerprint."
    )
    parser.add_argument(
        "--fingerprints", required=True, help="Comma-separated list of fingerprints to delete"
    )
    parser.add_argument("--comment", required=True, help="Comment associated with the deletion")
    args = parser.parse_args()
    fingerprints = args.fingerprints.split(",")
    invalid_fingerprints = []
    for fingerprint in fingerprints:
        # fingperints are usually of length 40 or 64 depending on the hash algorithm, and
        # consist of hexadecimal characters only.
        if not re.fullmatch(r"[0-9A-Fa-f]{40}|[0-9A-Fa-f]{64}", fingerprint):
            logging.error("Invalid fingerprint format: %s", fingerprint)
            invalid_fingerprints.append(fingerprint)
    if invalid_fingerprints:
        raise InvalidFingerprintError(invalid_fingerprints)

    comment = args.comment

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                delete_fingerprints(cursor, fingerprints, comment)
                remove_ptree_data()
                invoke_rebuild_prefix_tree()
    except (
        DatabaseConnectionError,
        DatabaseOperationError,
        PtreeDataError,
        PrefixTreeRebuildError,
    ) as e:
        logging.error("Unable to delete keys: %s", e)
        raise KeyDeletionError from e


if __name__ == "__main__":  # pragma: no cover
    main()
