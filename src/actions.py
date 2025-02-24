# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Hockeypuck charm actions."""

import logging
from typing import List

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

        charm.framework.observe(charm.on.block_keys_action, self._block_keys_action)
        charm.framework.observe(
            charm.on.rebuild_prefix_tree_action, self._rebuild_prefix_tree_action
        )

    def _block_keys_action(self, event: ops.ActionEvent) -> None:
        """Blacklist and delete keys from the database.

        Args:
            event: the event triggering the original action.
        """
        fingerprints = event.params["fingerprints"]
        comment = event.params["comment"]
        command = [
            "/hockeypuck/bin/delete_keys.py",
            "--fingerprints",
            fingerprints,
            "--comment",
            comment,
        ]
        self._execute_action(event, command)

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

    def _execute_action(self, event: ops.ActionEvent, command: List[str]) -> None:
        """Execute the action.

        Args:
            event: the event triggering the original action.
            command: the command to be executed inside the hockeypuck container.
        """
        if not self.charm.is_ready():
            event.fail("Service not yet ready.")
        hockeypuck_container = self.charm.unit.get_container(HOCKEYPUCK_CONTAINER_NAME)
        service_name = next(iter(hockeypuck_container.get_services()))
        try:
            _ = hockeypuck_container.pebble.stop_services(services=[service_name])
            process = hockeypuck_container.exec(
                command,
                service_context=service_name,
            )
            stdout, stderr = process.wait_output()
            logging.info(stdout)
            if stderr is None:
                logging.error("Action %s failed: %s", " ".join(command), stderr)
        except ops.pebble.ExecError as ex:
            logger.exception("Action %s failed: %s %s", ex.command, ex.stdout, ex.stderr)
            event.fail(f"Failed: {ex.stderr!r}")
        finally:
            _ = hockeypuck_container.pebble.start_services(services=[service_name])
