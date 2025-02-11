# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Hockeypuck charm actions."""

import logging

import ops
import paas_app_charmer.go

logger = logging.getLogger(__name__)

HOCKEYPUCK_CONTAINER_NAME = "app"


class Observer(ops.Object):
    """Charm actions observer."""

    def __init__(self, charm: paas_app_charmer.go.Charm):
        """Initialize the observer and register actions handlers.

        Args:
            charm: The parent charm to attach the observer to.
        """
        super().__init__(charm, "actions-observer")
        self.charm = charm

        charm.framework.observe(
            charm.on.blacklist_and_delete_key_action, self._blacklist_and_delete_key_action
        )
        charm.framework.observe(
            charm.on.rebuild_prefix_tree_action, self._rebuild_prefix_tree_action
        )

    def _blacklist_and_delete_key_action(self, event: ops.ActionEvent) -> None:
        """Blacklist and delete a key/s from the database.

        Args:
            event: the event triggering the original action.
        """
        keys = event.params["fingerprint"]
        keys_list = [key for key in keys.split("\n")]
        pass

    def _rebuild_prefix_tree_action(self, event: ops.ActionEvent) -> None:
        """Rebuild the prefix tree using the hockeypuck-pbuild binary.

        Args:
            event: the event triggering the original action.
        """
        if not self.charm.is_ready():
            event.fail("Service not yet ready.")
        service_name = next(iter(self.charm._container.get_services()))
        try:
            _ = self.charm._container.pebble.stop_services(services=[service_name])
            command = [
                "/hockeypuck/bin/hockeypuck-pbuild",
                "-config",
                "/hockeypuck/etc/hockeypuck.conf",
            ]
            process = self.charm._container.exec(
                command,
                environment=self.charm._gen_environment(),
            )
            _, _ = process.wait_output()
        except ops.pebble.ExecError as ex:
            logger.exception("Action %s failed: %s %s", ex.command, ex.stdout, ex.stderr)
            event.fail(f"Failed: {ex.stderr!r}")
        finally:
            _ = self.charm._container.pebble.start_services(services=[service_name])
