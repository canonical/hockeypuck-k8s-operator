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
import sys
from typing import List

import psycopg2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PTREE_DATA_DIR = "/hockeypuck/data/ptree"


def remove_ptree_data() -> None:
    """Remove all data from the ptree directory.

    Raises:
        FileNotFoundError: if the ptree data directory does not exist.
        OSError: if the deletion operation fails.
    """
    if not os.path.exists(PTREE_DATA_DIR):
        raise FileNotFoundError(f"Ptree data directory does not exist: {PTREE_DATA_DIR}")
    for filename in os.listdir(PTREE_DATA_DIR):
        file_path = os.path.join(PTREE_DATA_DIR, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except OSError as e:
            raise OSError(f"Failed to delete {file_path}: {e}") from e


def invoke_rebuild_prefix_tree() -> None:
    """Invoke the prefix_tree_rebuild binary.

    Raises:
        RuntimeError: if the rebuild operation fails.
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
        raise RuntimeError(f"prefix_tree_rebuild failed with return code: {result}")
    logging.info("prefix_tree_rebuild invoked successfully.")


def get_db_connection() -> psycopg2.extensions.connection:
    """Connect to the Postgres database.

    Returns:
        psycopg2.extensions.connection: the database connection.

    Raises:
        OperationalError: if the connection fails.
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
        raise psycopg2.OperationalError(f"Failed to connect to database: {e}")


def delete_fingerprints(
    cursor: psycopg2.extensions.cursor, fingerprints: List[str], comment: str
) -> None:
    """Delete fingerprints from the database.

    Args:
        cursor: the database cursor.
        fingerprints: list of fingerprints to delete.
        comment: the comment associated with the deletion.

    Raises:
        Error: if any SQL command fails.
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
        raise psycopg2.Error(f"Error executing SQL commands: {e}")


def main() -> None:
    """Main entrypoint.

    Raises:
        psycopg2.Error: if any database operation fails.
        FileNotFoundError: if the ptree data directory does not exist.
        OSError
        RuntimeError: if the rebuild operation fails.
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
    invalid = 0
    for fingerprint in fingerprints:
        # fingperints are usually of length 40 or 64 depending on the hash algorithm, and
        # consist of hexadecimal characters only.
        if not re.fullmatch(r"[0-9A-Fa-f]{40}|[0-9A-Fa-f]{64}", fingerprint):
            logging.error("Invalid fingerprint format: %s", fingerprint)
            invalid = 1
    if invalid:
        sys.exit(1)

    comment = args.comment

    with get_db_connection() as conn:
        if conn is None:
            logging.error("Database connection failed. Exiting.")
            sys.exit(1)
        else:
            with conn.cursor() as cursor:
                try:
                    delete_fingerprints(cursor, fingerprints, comment)
                    remove_ptree_data()
                    invoke_rebuild_prefix_tree()
                except psycopg2.Error as e:
                    logging.error("Failed to delete fingerprints: %s", e)
                    raise
                except (OSError, FileNotFoundError) as e:
                    logging.error("Failed to remove ptree data: %s", e)
                    raise
                except RuntimeError as e:
                    logging.error("Failed to invoke rebuild prefix tree: %s", e)
                    raise


if __name__ == "__main__":  # pragma: no cover
    main()
