# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Hockeypuck charm utilities."""

import logging

import ops
import paas_app_charmer.go

logger = logging.getLogger(__name__)


def get_blacklisted_keys(charm: paas_app_charmer.go.Charm) -> str:
    """Retrieve blacklisted keys from the postgres database.

    Args:
        charm: The parent charm.

    Returns:
        Comma-seperated string of blacklisted keys.
    """
    if "postgresql" in charm.model.relations:
        command = [
            "/hockeypuck/bin/retrieve_blacklisted_keys",
        ]
        try:
            process = charm._container.exec(
                command,
                environment=charm._gen_environment(),
            )
            blacklisted_keys, _ = process.wait_output()
        except ops.pebble.ExecError as ex:
            logger.exception(
                "Failed to retrieve blacklisted keys. Output: %s, Error: %s",
                ex.stdout,
                ex.stderr,
            )
        return blacklisted_keys
    else:
        return ""
