# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Hockeypuck charm actions."""

import logging
import typing

import ops
import paas_app_charmer.go
import requests
from paas_charm.go.charm import WORKLOAD_CONTAINER_NAME

from admin_gpg import AdminGPG
from block_keys import InvalidFingerprintError, KeyBlockError, block_keys, check_valid_fingerprints

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
        try:
            input_fingerprints: str = event.params["fingerprints"]
            comment: str = event.params["comment"]
            fingerprints = input_fingerprints.split(",")
            check_valid_fingerprints(fingerprints=fingerprints)
            if not self.charm.is_ready():
                raise RuntimeError("Service not yet ready.")
            for fingerprint in fingerprints:
                response = requests.get(
                    f"http://127.0.0.1:{HTTP_PORT}/pks/lookup?op=get&search=0x{fingerprint}",
                    timeout=20,
                )
                response.raise_for_status()
                if "-----BEGIN PGP PUBLIC KEY BLOCK-----" in response.text:
                    public_key = response.text
                    request = "/pks/delete\n" + public_key
                    admin_gpg = AdminGPG(self.model)
                    signature = admin_gpg.generate_signature(request=request)
                    response = requests.delete(
                        f"http://127.0.0.1:{HTTP_PORT}/pks/delete",
                        timeout=20,
                        data={"keytext": request, "keysig": signature},
                    )
                    response.raise_for_status()
                else:
                    raise RuntimeError("Public key not found in response")
            db_credentials = self._retrieve_postgresql_credentials()
            block_keys(fingerprints=fingerprints, comment=comment, db_credentials=db_credentials)
        except (
            InvalidFingerprintError,
            RuntimeError,
            KeyBlockError,
            requests.exceptions.RequestException,
        ) as e:
            logger.exception("Action failed: %s", e)
            event.fail(f"Failed: {e}")

    def _retrieve_postgresql_credentials(self) -> None | dict[str, str]:
        """Retrieve PostgreSQL connection details from the relation."""
        relation = self.model.get_relation("database")
        if not relation:
            return None
        postgresql_app = relation.app
        if not postgresql_app:
            return None
        relation_data = relation.data[postgresql_app]
        db_name = relation_data.get("POSTGRESQL_DB_NAME")
        db_hostname = relation_data.get("POSTGRESQL_DB_HOSTNAME")
        db_username = relation_data.get("POSTGRESQL_DB_USERNAME")
        db_password = relation_data.get("POSTGRESQL_DB_PASSWORD")
        if None in (db_name, db_hostname, db_username, db_password):
            return None
        return {
            "db-name": str(db_name),
            "db-hostname": str(db_hostname),
            "db-username": str(db_username),
            "db-password": str(db_password),
        }

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

    def _lookup_key_action(self, event: ops.ActionEvent) -> None:
        """Lookup a key in the hockeypuck database using email id or fingerprint or keyword.

        Args:
            event: the event triggering the original action.
        """
        keyword = event.params["keyword"]
        if not self.charm.is_ready():
            event.fail("Service not yet ready.")
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

    def _execute_action(self, event: ops.ActionEvent, command: list[str]) -> None:
        """Stop the hockeypuck service, execute the action and start the service.

        Args:
            event: the event triggering the original action.
            command: the command to be executed inside the hockeypuck container.
        """
        if not self.charm.is_ready():
            event.fail("Service not yet ready.")
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
