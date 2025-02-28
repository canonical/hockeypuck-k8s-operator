#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""This script cleans up the /data/ptree folder and rebuilds the prefix tree."""

import logging
import os
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


PTREE_DATA_DIR = "/hockeypuck/data/ptree"


class PrefixTreeRebuildError(Exception):
    """Exception raised for errors in the prefix tree rebuild operation."""


def remove_ptree_data() -> None:
    """Remove all data from the ptree directory.

    Raises:
        PrefixTreeRebuildError: if the ptree data directory does not exist or deletion fails.
    """
    if not os.path.exists(PTREE_DATA_DIR):
        raise PrefixTreeRebuildError(f"Ptree data directory does not exist: {PTREE_DATA_DIR}")
    for filename in os.listdir(PTREE_DATA_DIR):
        file_path = os.path.join(PTREE_DATA_DIR, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except OSError as e:
            raise PrefixTreeRebuildError(f"Failed to delete {file_path}: {e}") from e


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


def main() -> None:
    """Main entrypoint.

    Raises:
        PrefixTreeRebuildError: if the key deletion operation fails.
    """
    try:
        remove_ptree_data()
        invoke_rebuild_prefix_tree()
    except PrefixTreeRebuildError as e:
        logging.error("Unable to delete keys: %s", e)
        raise PrefixTreeRebuildError(f"Unable to delete keys: {e}") from e


if __name__ == "__main__":  # pragma: no cover
    main()
