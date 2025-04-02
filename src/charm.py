#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

# pylint: disable=protected-access

"""Go Charm entrypoint."""

import logging
import pathlib
import subprocess
import typing

import ops
import paas_charm.go
from paas_charm.charm_state import CharmState

import actions
import traefik_route_observer
from admin_gpg import AdminGPG

logger = logging.getLogger(__name__)


class HockeypuckK8SCharm(paas_charm.go.Charm):
    """Go Charm service."""

    def __init__(self, *args: typing.Any) -> None:
        """Initialize the instance.

        Args:
            args: passthrough to CharmBase.
        """
        super().__init__(*args)
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "gnupg", "-y"], check=True)
        self.actions_observer = actions.Observer(self)
        self._traefik_route = traefik_route_observer.TraefikRouteObserver(self)
        self.admin_gpg = AdminGPG(self.model)

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
        if self.is_ready():
            response_code = self.admin_gpg.push_admin_key()
            if response_code != 200:
                ops.ErrorStatus("Unable to push admin key to Hockeypuck")

    def get_cos_dir(self) -> str:
        """Return the directory with COS related files.

        Returns:
            Return the directory with COS related files.
        """
        return str((pathlib.Path(__file__).parent / "cos").absolute())

    def _create_charm_state(self) -> CharmState:
        """Create charm state.

        Create charm state and add the admin key generated to the charm state's user
        defined config.
        This method may raise CharmConfigInvalidError.

        Returns:
            New CharmState
        """
        charm_state = super()._create_charm_state()
        if "admin_keys" not in charm_state._user_defined_config:
            charm_state._user_defined_config["admin_keys"] = self.admin_gpg.admin_fingerprint
        else:
            charm_state._user_defined_config["admin_keys"] = (
                charm_state._user_defined_config["admin_keys"].rstrip(chars=",")
                + f",{self.admin_gpg.admin_fingerprint}"
            )

        return charm_state


if __name__ == "__main__":
    ops.main(HockeypuckK8SCharm)
