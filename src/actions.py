# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Hockeypuck charm actions."""

import logging
import re
import typing

import ops
import paas_app_charmer.go
import requests
from requests.exceptions import RequestException

from admin_gpg import AdminGPG

WORKLOAD_CONTAINER_NAME = "app"

logger = logging.getLogger(__name__)

HTTP_PORT: typing.Final[int] = 11371  # the port hockeypuck listens to for HTTP requests
RECONCILIATION_PORT: typing.Final[int] = 11370  # the port hockeypuck listens to for reconciliation
METRICS_PORT: typing.Final[int] = 9626  # the metrics port
FINGERPRINT_REGEX = re.compile(r"[0-9A-Fa-f]{40}|[0-9A-Fa-f]{64}")


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
            if not self.charm.is_ready():
                raise RuntimeError("Service not yet ready.")

            input_fingerprints: str = event.params["fingerprints"]
            comment: str = event.params["comment"]
            fingerprints = input_fingerprints.split(",")

            result = {}
            fingerprints = [fingerprint.lower() for fingerprint in fingerprints]
            for fingerprint in fingerprints:
                if not FINGERPRINT_REGEX.fullmatch(fingerprint):
                    result[fingerprint] = (
                        "Invalid fingerprint format. "
                        "Fingerprints must be 40 or 64 characters long and "
                        "consist of hexadecimal characters only."
                    )
                    continue
                response = requests.get(
                    f"http://127.0.0.1:{HTTP_PORT}/pks/lookup?op=get&search=0x{fingerprint}",
                    timeout=20,
                )
                if response.status_code == 404:
                    result[fingerprint] = "Fingerprint unavailable in the database."
                    continue
                if not response.ok:
                    response.raise_for_status()
                if "-----BEGIN PGP PUBLIC KEY BLOCK-----" in response.text:
                    public_key = response.text
                    request = "/pks/delete\n" + public_key
                    admin_gpg = AdminGPG(self.model)
                    signature = admin_gpg.generate_signature(request=request)
                    response = requests.post(
                        f"http://127.0.0.1:{HTTP_PORT}/pks/delete",
                        timeout=20,
                        data={"keytext": request, "keysig": signature},
                    )
                    response.raise_for_status()
                    logging.info("Deleted %s from the database.", fingerprint)
                    event.log(f"Deleted {fingerprint} from the database.")
                else:
                    raise RuntimeError(
                        f"Public key not found in response for fingerprint: {fingerprint}"
                    )
            fingerprints_to_block = list(set(fingerprints) - set(result))

            command = [
                "/hockeypuck/bin/block_keys.py",
                "--fingerprints",
                ",".join(fingerprints_to_block),
                "--comment",
                comment,
            ]
            self._execute_action(event, command)
            for fingerprint in fingerprints_to_block:
                result[fingerprint] = "Deleted and blocked successfully."
            event.set_results(result)
        except (
            RuntimeError,
            RequestException,
        ) as e:
            logger.exception("Action failed: %s", e)
            event.fail(f"Failed: {e}")

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
        except RequestException as e:
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
