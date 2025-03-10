# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Hockeypuck charm actions."""

import logging
import typing

import ops
import paas_app_charmer.go
import requests
from paas_charm.go.charm import WORKLOAD_CONTAINER_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HTTP_PORT: typing.Final[int] = 11371  # the port hockeypuck listens to for HTTP requests
RECONCILIATION_PORT: typing.Final[int] = 11370  # the port hockeypuck listens to for reconciliation
METRICS_PORT: typing.Final[int] = 9626  # the metrics port


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
        charm.framework.observe(charm.on.lookup_key_action, self._lookup_key_action)

    def _block_keys_action(self, event: ops.ActionEvent) -> None:
        """Blocklist and delete keys from the database.

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
        self._execute_action(event, command, leader_only=True)
        command = ["/hockeypuck/bin/rebuild_prefix_tree.py"]
        self._execute_action(event, command)

    def _rebuild_prefix_tree_action(self, event: ops.ActionEvent) -> None:
        """Rebuild the prefix tree using the hockeypuck-pbuild binary.

        Args:
            event: the event triggering the original action.
        """
        command = ["/hockeypuck/bin/rebuild_prefix_tree.py"]
        self._execute_action(event, command)

    def _lookup_key_action(self, event: ops.ActionEvent) -> None:
        """Lookup a key in the hockeypuck database using email id or fingerprint or keyword.

        Args:
            event: the event triggering the original action.
        """
        keyword = event.params["keyword"]
        try:
            response = requests.get(
                f"http://127.0.0.1:{HTTP_PORT}/pks/lookup?op=get&search={keyword}",
                timeout=20,
            )
            response.raise_for_status()
            event.set_results({"result": response.text})
        except requests.exceptions.RequestException as e:
            logger.error("Action failed: %s", e)
            event.fail(f"Failed: {str(e)}")

    def _execute_action(
        self, event: ops.ActionEvent, command: list[str], leader_only: bool = False
    ) -> None:
        """Stop the hockeypuck service, execute the action and start the service.

        Args:
            event: the event triggering the original action.
            command: the command to be executed inside the hockeypuck container.
            leader_only: whether the action should be executed only by the leader unit.
        """
        if not self.charm.is_ready():
            event.fail("Service not yet ready.")
        if leader_only and not self.charm.unit.is_leader():
            return
        hockeypuck_container = self.charm.unit.get_container(WORKLOAD_CONTAINER_NAME)
        service_name = next(iter(hockeypuck_container.get_services()))
        try:
            hockeypuck_container.pebble.stop_services(services=[service_name])
            process = hockeypuck_container.exec(
                command,
                service_context=service_name,
            )
            process.wait_output()
        except ops.pebble.ExecError as ex:
            logger.exception("Action %s failed: %s %s", ex.command, ex.stdout, ex.stderr)
            event.fail(f"Failed: {ex.stderr!r}")
        finally:
            hockeypuck_container.pebble.start_services(services=[service_name])
