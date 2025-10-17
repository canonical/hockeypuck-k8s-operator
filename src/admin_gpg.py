#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Admin GPG Module."""


import logging
import time
import typing

import gnupg
import ops
import requests
from passlib.pwd import genword
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

ADMIN_LABEL = "admin-gpg-key"


class AdminGPG:
    """Admin GPG class."""

    def __init__(self, model: ops.Model) -> None:
        """Initialize the AdminGPG class.

        Args:
            model: The Juju model.
        """
        self.model = model
        self.gpg = gnupg.GPG()

    def admin_fingerprint(self) -> str:
        """Get the admin GPG key fingerprint.

        Returns:
            The fingerprint of the admin GPG key.
        """
        return self._ensure_admin_key_in_keyring()

    def _ensure_admin_key_in_keyring(self) -> str:
        """Ensure the admin GPG key is present in the GPG keyring.

        Checks if the admin GPG key is already present in the Juju secrets. If present,
        the key is loaded into the keyring, else a new key is generated and added
        to the Juju secrets. The newly generated key by default gets added to the keyring.

        Returns:
            The fingerprint of the admin GPG key.
        """
        try:
            admin_secret = self.model.get_secret(label=ADMIN_LABEL)
        except ops.SecretNotFoundError:
            admin_secret = None
        try:
            if admin_secret is None:
                admin_credentials = self._create_admin_gpg_key()
                self._add_admin_to_juju_secret(admin_credentials)
                return admin_credentials["admin-key"].fingerprint

            admin_credentials = admin_secret.get_content()
            self.gpg.import_keys(admin_credentials["adminpublickey"])
            self.gpg.import_keys(admin_credentials["adminprivatekey"])
            return admin_credentials["adminfingerprint"]
        except ValueError as e:
            logging.error("Error adding GPG key to secret: %s", e)
            raise e

    def _create_admin_gpg_key(self) -> dict[str, typing.Any]:
        """Generate a new GPG key for admin and return the admin credentials.

        Returns:
            The admin credentials.
        """
        password = genword(length=10)
        input_data = self.gpg.gen_key_input(
            name_real="Admin User", name_email="admin@user.com", passphrase=password
        )
        key = self.gpg.gen_key(input_data)
        return {"admin-key": key, "password": password}

    def _add_admin_to_juju_secret(self, admin_credentials: dict[str, typing.Any]) -> None:
        """Add the admin key to the juju secret store.

        Args:
            admin_credentials: The admin credentials to add to the juju secret store.
        """
        try:
            admin_key = admin_credentials["admin-key"]
            admin_password = admin_credentials["password"]

            admin_public_key = self.gpg.export_keys(admin_key.fingerprint)
            admin_private_key = self.gpg.export_keys(  # pylint: disable=unexpected-keyword-arg
                admin_key.fingerprint,
                secret=True,
                passphrase=admin_password,
            )

            # juju secrets don't allow underscores or hyphens in the key name
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

    def push_admin_key(self, num_tries: int = 5) -> None:
        """Push the admin public key to the keyserver.

        Args:
            num_tries: Number of times to retry pushing the admin key to Hockeypuck.

        Raises:
            RequestException: If there is an error pushing the admin key to Hockeypuck.
            RuntimeError: If the admin GPG key is not found in Juju secret store.
        """
        try:
            admin_secret = self.model.get_secret(label=ADMIN_LABEL).get_content()
            public_key = admin_secret["adminpublickey"]
            trial = 0
            while trial < num_tries:
                response = requests.post(
                    "http://127.0.0.1:11371/pks/add",
                    timeout=20,
                    data={"keytext": public_key},
                )
                logging.info(
                    "Pushing admin key to hockeypuck. Response text: %s, response code: %s",
                    response.text,
                    response.status_code,
                )
                if response.status_code == 200:
                    return
                trial += 1
                logging.info("Waiting for Hockeypuck to be reachable")
                time.sleep(5)
            if trial == num_tries:
                response.raise_for_status()
        except RequestException as e:
            logging.error("Error pushing admin key to Hockeypuck: %s", e)
            raise RequestException(f"Failed to push admin key to Hockeypuck: {e}") from e
        except ops.SecretNotFoundError as e:
            raise RuntimeError(f"Admin GPG key not found in Juju secret store. {e}") from e

    def generate_signature(self, request: str) -> str:
        """Generate signature for the given request.

        Args:
            request: The request to sign.

        Returns:
            The signature for the given request.
        """
        admin_secret = self.model.get_secret(label=ADMIN_LABEL).get_content()
        password = admin_secret["adminpassword"]
        signature = self.gpg.sign(
            request,
            keyid=self.admin_fingerprint(),
            passphrase=password,
            detach=True,
        )
        return str(signature)
