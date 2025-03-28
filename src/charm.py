#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

# pylint: disable=protected-access

"""Go Charm entrypoint."""

import logging
import pathlib
import subprocess
import typing

import gnupg
import ops
import paas_charm.go
import requests
from ops.model import Secret
from paas_charm.charm_state import CharmState
from passlib.pwd import genword

import actions
import traefik_route_observer

logger = logging.getLogger(__name__)

ADMIN_LABEL = "admin-gpg-key"


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
        self.framework.observe(
            self.on[self._workload_config.container_name].pebble_ready, self._on_pebble_ready
        )

    def _on_pebble_ready(self, event: ops.framework.EventBase) -> None:
        """Handle GPG admin key on pebble_ready event."""
        try:
            admin_secret = self._get_admin_juju_secret()
            gpg = gnupg.GPG()
            if admin_secret is None:
                admin_credentials = self._generate_admin_gpg_key()
                self._add_admin_to_juju_secret(admin_credentials)
                admin_public_key = gpg.export_keys(admin_credentials["admin-key"].fingerprint)
            else:
                # Add admin key to the GPG keyring
                admin_credentials = admin_secret.get_content()
                admin_public_key = gpg.import_keys(admin_credentials["adminpublickey"])
                _ = gpg.import_keys(admin_credentials["adminprivatekey"])

            super()._on_pebble_ready(event)
            self._push_admin_public_key(admin_public_key)
        except ValueError as e:
            logging.error("Error adding GPG key to secret: %s", e)
            raise e

    def _add_admin_to_juju_secret(self, admin_credentials: dict[str, typing.Any]) -> None:
        """Add the admin key to the juju secret store.

        Args:
            admin_credentials: The admin credentials to add to the juju secret store.
        """
        try:
            gpg = gnupg.GPG()
            admin_key = admin_credentials["admin-key"]
            admin_password = admin_credentials["password"]

            admin_public_key = gpg.export_keys(admin_key.fingerprint)
            admin_private_key = gpg.export_keys(  # pylint: disable=unexpected-keyword-arg
                admin_key.fingerprint,
                secret=True,
                passphrase=admin_password,
            )

            # juju secrets dont allow underscores or hyphens in the key name
            self.model.app.add_secret(
                {
                    "adminpublickey": admin_public_key,
                    "adminprivatekey": admin_private_key,
                    "adminfingerprint": admin_key.fingerprint,
                    "adminpassword": admin_password,
                },
                label=ADMIN_LABEL,
            )
        except ValueError as e:
            logging.error("Error adding GPG key to secret: %s", e)
            raise e

    def _generate_admin_gpg_key(self) -> dict[str, typing.Any]:
        """Generate a new GPG key for admin and return the admin credentials."""
        logger.info("Generating new GPG key for admin.")
        gpg = gnupg.GPG()
        password = genword(length=10)
        input_data = gpg.gen_key_input(
            name_real="Admin User", name_email="admin@user.com", passphrase=password
        )
        key = gpg.gen_key(input_data)
        return {"admin-key": key, "password": password}

    def _push_admin_public_key(self, public_key: str) -> None:
        """Push the admin public key to the keyserver."""
        try:
            response = requests.post(
                "http://127.0.0.1:11371/pks/add",
                timeout=20,
                data={"keytext": public_key},
            )
            if response.status_code in (200, 409):
                return

            response.raise_for_status()

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to push admin key to hockeypuck: {e}") from e

    def _get_admin_juju_secret(self) -> Secret | None:
        """Get the admin GPG key from the juju secret store.

        Returns:
            The admin GPG key from the juju secret store.
        """
        try:
            admin_secret = self.model.get_secret(label=ADMIN_LABEL)
        except ops.SecretNotFoundError:
            admin_secret = None
        return admin_secret

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

    def _create_charm_state(self) -> CharmState:
        """Create charm state.

        Create charm state and add charm generated admin key to the charm state's user
        defined config.
        This method may raise CharmConfigInvalidError.

        Returns:
            New CharmState
        """
        charm_state = super()._create_charm_state()
        admin_secret = self._get_admin_juju_secret()
        if admin_secret is not None:
            admin_fingerprint = admin_secret.get_content()["adminfingerprint"]
            if "admin_keys" not in charm_state._user_defined_config:
                charm_state._user_defined_config["admin_keys"] = admin_fingerprint
            else:
                charm_state._user_defined_config["admin_keys"] = (
                    charm_state._user_defined_config["admin_keys"].rstrip(chars=",")
                    + f",{admin_fingerprint}"
                )

        return charm_state


if __name__ == "__main__":
    ops.main(HockeypuckK8SCharm)
