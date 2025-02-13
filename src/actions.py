# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Hockeypuck charm actions."""

# pylint: disable=protected-access

import logging
from typing import Any, Dict, List

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
        """Blacklist and delete keys from the database.

        Args:
            event: the event triggering the original action.
        """
        fingerprints = event.params["fingerprints"]
        ticket_id = event.params["ticket-id"]
        env = {"TICKET_ID": ticket_id, "APP_DELETE_FINGERPRINTS": fingerprints}
        command = [
            "/hockeypuck/bin/delete_keys",
        ]
        self._execute_action(event, command, env)

    def _rebuild_prefix_tree_action(self, event: ops.ActionEvent) -> None:
        """Rebuild the prefix tree using the hockeypuck-pbuild binary.

        Args:
            event: the event triggering the original action.
        """
        command = [
            "/hockeypuck/bin/hockeypuck-pbuild",
            "-config",
            "/hockeypuck/etc/hockeypuck.conf",
        ]
        self._execute_action(event, command)

    def _execute_action(
        self, event: ops.ActionEvent, command: List[str], env: Dict[str, Any] | None = None
    ) -> None:
        """Execute the action.

        Args:
            event: the event triggering the original action.
            command: the command to be executed inside the hockeypuck container.
            env (optional): Any extra environment variables to be passed to the command.
        """
        if not self.charm.is_ready():
            event.fail("Service not yet ready.")
        hockeypuck_container = self.charm.unit.containers[HOCKEYPUCK_CONTAINER_NAME]
        service_name = next(iter(hockeypuck_container.get_services()))
        try:

            _ = hockeypuck_container.pebble.stop_services(services=[service_name])
            environment = self.charm._gen_environment()
            if env is not None:
                environment.update(env)
            process = hockeypuck_container.exec(
                command,
                environment=environment,
            )
            _, _ = process.wait_output()
        except ops.pebble.ExecError as ex:
            logger.exception("Action %s failed: %s %s", ex.command, ex.stdout, ex.stderr)
            event.fail(f"Failed: {ex.stderr!r}")
        finally:
            _ = hockeypuck_container.pebble.start_services(services=[service_name])
