#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Go Charm entrypoint."""

import logging
import typing

import ops
import paas_charm.go

logger = logging.getLogger(__name__)

RECONCILIATION_PORT: typing.Final[int] = 11370  # the port hockeypuck listens to for reconciliation


class HockeypuckK8SCharm(paas_charm.go.Charm):
    """Go Charm service."""

    def restart(self, rerun_migrations: bool = False) -> None:
        """Open reconciliation port and call the parent restart method.

        Args:
            rerun_migrations: Whether to rerun migrations.
        """
        self.unit.open_port("tcp", RECONCILIATION_PORT)
        super().restart(rerun_migrations)


if __name__ == "__main__":
    ops.main(HockeypuckK8SCharm)
