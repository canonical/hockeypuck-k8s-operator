#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Go Charm entrypoint."""

import logging
import typing

import ops
import paas_charm.go
from paas_charm.charm_state import CharmState

import actions
import utils

logger = logging.getLogger(__name__)

RECONCILIATION_PORT: typing.Final[int] = 11370  # the port hockeypuck listens to for reconciliation


class HockeypuckK8SCharm(paas_charm.go.Charm):
    """Go Charm service."""

    def __init__(self, *args: typing.Any) -> None:
        """Initialize the instance.

        Args:
            args: passthrough to CharmBase.
        """
        super().__init__(*args)
        self.actions_observer = actions.Observer(self)

    def _create_charm_state(self) -> CharmState:
        charm_state = super()._create_charm_state()
        blacklisted_fingerprints = utils.get_blacklisted_keys(self)
        logging.info("Fingerprints: %s", blacklisted_fingerprints)
        charm_state._app_config["APP_BLACKLIST_FINGERPRINTS"] = blacklisted_fingerprints
        return charm_state

    def restart(self, rerun_migrations: bool = False) -> None:
        """Open reconciliation port and call the parent restart method.

        Args:
            rerun_migrations: Whether to rerun migrations.
        """
        self.unit.open_port("tcp", RECONCILIATION_PORT)
        super().restart(rerun_migrations)


if __name__ == "__main__":
    ops.main(HockeypuckK8SCharm)
