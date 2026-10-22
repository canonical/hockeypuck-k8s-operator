#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

# pylint: disable=protected-access

"""Go Charm entrypoint."""

import logging
import typing

import ops
import paas_charm.go
from charms.operator_libs_linux.v0 import apt
from paas_charm.charm_state import CharmState
from requests.exceptions import RequestException

import actions
import reconciliation_route
from admin_gpg import AdminGPG

logger = logging.getLogger(__name__)

# By default, the logging level is set to DEBUG for all loggers in the
# logging.root.manager.loggerDict dictionary. This is too verbose for
# production workloads.
# (https://github.com/canonical/operator/blob/main/ops/log.py#L42).
for logger_name in getattr(logging.root.manager, "loggerDict", {}):
    logging.getLogger(logger_name).setLevel(logging.INFO)


class HockeypuckK8SCharm(paas_charm.go.Charm):
    """Go Charm service.

    Attrs:
        custom_relations: Custom relations handled by the charm.
    """

    custom_relations = [reconciliation_route.ReconciliationRouteRelation]

    def __init__(self, *args: typing.Any) -> None:
        """Initialize the instance.

        Args:
            args: passthrough to CharmBase.
        """
        super().__init__(*args)

        self.actions_observer = actions.Observer(self)
        self.framework.observe(self.on.install, self.install_gnupg)
        self.framework.observe(self.on.upgrade_charm, self.install_gnupg)

    def install_gnupg(self, _: ops.InstallEvent) -> None:
        """Install gnupg package."""
        # The python-gnupg package requires gnupg package to be installed.
        # Charmcraft currently does not support staging packages in charmcraft.yaml.
        # See https://github.com/canonical/charmcraft/issues/1990
        apt.update()
        apt.add_package(["gnupg"])

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

    def _reconcile(self, rerun_migrations: bool = False) -> None:
        """Open reconciliation port and call the parent reconcile method.

        Args:
            rerun_migrations: Whether to rerun migrations.

        Raises:
            RequestException: If the admin key can't be pushed to Hockeypuck.
        """
        super()._reconcile(rerun_migrations)
        # paas-charm sets the unit ports to the application port only, so the reconciliation
        # port has to be opened after it. Juju applies port changes once the hook finishes.
        self.unit.open_port("tcp", actions.RECONCILIATION_PORT)
        # The parent reconcile leaves the unit active only if the workload was restarted.
        if not isinstance(self.unit.status, ops.ActiveStatus):
            return
        try:
            AdminGPG(self.model).push_admin_key()
        except RequestException:
            logger.exception("Unable to push admin key to Hockeypuck")
            raise

    def _create_charm_state(self) -> CharmState:
        """Create charm state.

        Create charm state and add the admin key generated to the charm state's user
        defined config.
        This method may raise CharmConfigInvalidError.

        Returns:
            New CharmState
        """
        charm_state = super()._create_charm_state()
        config = charm_state.user_defined_config
        user_keys = str(config.get("admin_keys", "")).rstrip(",")
        admin_fingerprint = AdminGPG(self.model).admin_fingerprint()
        config["admin_keys"] = ",".join(filter(None, [user_keys, admin_fingerprint]))

        return charm_state


if __name__ == "__main__":
    ops.main(HockeypuckK8SCharm)
