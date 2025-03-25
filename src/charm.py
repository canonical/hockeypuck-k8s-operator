#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Go Charm entrypoint."""

import logging
import pathlib
import typing

import ops
import paas_charm.go

import actions
import traefik_route_observer

logger = logging.getLogger(__name__)


class HockeypuckK8SCharm(paas_charm.go.Charm):
    """Go Charm service."""

    def __init__(self, *args: typing.Any) -> None:
        """Initialize the instance.

        Args:
            args: passthrough to CharmBase.
        """
        super().__init__(*args)
        self.actions_observer = actions.Observer(self)
        self._traefik_route = traefik_route_observer.TraefikRouteObserver(self)

    def is_ready(self) -> bool:
        """Check if the charm is ready to start the workload application.

        Returns:
            True if the charm is ready to start the workload application.
        """
        if self.model.app.planned_units() > 1:
            self.update_app_and_unit_status(
                ops.BlockedStatus("Hockeypuck does not support multi-unit deployments")
            )
            return False
        return super().is_ready()

    def restart(self, rerun_migrations: bool = False) -> None:
        """Open reconciliation port and call the parent restart method.

        Args:
            rerun_migrations: Whether to rerun migrations.
        """
        self.unit.open_port("tcp", actions.RECONCILIATION_PORT)
        super().restart(rerun_migrations)

    def get_cos_dir(self) -> str:
        """Return the directory with COS related files.

        Returns:
            Return the directory with COS related files.
        """
        return str((pathlib.Path(__file__).parent / "cos").absolute())


if __name__ == "__main__":
    ops.main(HockeypuckK8SCharm)
