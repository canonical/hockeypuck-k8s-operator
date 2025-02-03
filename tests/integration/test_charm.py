#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests."""

import logging
from typing import Dict

import pytest
import requests
from gnupg import GPG

logger = logging.getLogger(__name__)


@pytest.mark.abort_on_fail
@pytest.mark.usefixtures("hockeypuck_k8s_app")
async def test_hockeypuck_health() -> None:
    """
    arrange: Build and deploy the Hockeypuck charm.
    act: Send a request to the main page.
    assert: Returns 200 and the page contains the title.
    """
    response = requests.get(
        "http://127.0.0.1/",
        timeout=5,
        headers={"Host": "hockeypuck.local"},
    )
    assert response.status_code == 200
    assert "<title>OpenPGP Keyserver</title>" in response.text


@pytest.mark.usefixtures("hockeypuck_k8s_app")
async def test_adding_records(gpg_key: Dict) -> None:
    """
    arrange: Create a GPG Key
    act: Send a request to add a PGP key and lookup the key using the API
    assert: API is added successfully and lookup of key returns the key.
    """
    gpg = GPG()
    public_key = gpg.export_keys(gpg_key.fingerprint)
    response = requests.post(
        "http://127.0.0.1/pks/add",
        timeout=20,
        headers={"Host": "hockeypuck.local"},
        data={"keytext": public_key},
    )
    assert response.status_code == 200

    response = requests.get(
        f"http://127.0.0.1/pks/lookup?op=get&search=0x{gpg_key.fingerprint}",
        timeout=20,
        headers={"Host": "hockeypuck.local"},
    )

    assert response.status_code == 200
    assert "BEGIN PGP PUBLIC KEY BLOCK" in response.text
