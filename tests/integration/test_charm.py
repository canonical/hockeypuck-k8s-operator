#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests."""

import json
import logging
import socket
import typing
from typing import Any

import pytest
import requests
from gnupg import GPG
from juju.application import Application
from juju.client._definitions import UnitStatus

from actions import HTTP_PORT, RECONCILIATION_PORT

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
@pytest.mark.dependency(name="test_adding_records")
async def test_adding_records(gpg_key: Any) -> None:
    """
    arrange: Create a GPG Key
    act: Send a request to add a PGP key and lookup the key using the API
    assert: API is added successfully and lookup of key returns the key.
    """
    gpg = GPG()
    fingerprint = gpg_key.fingerprint
    public_key = gpg.export_keys(fingerprint)
    response = requests.post(
        "http://127.0.0.1/pks/add",
        timeout=20,
        headers={"Host": "hockeypuck.local"},
        data={"keytext": public_key},
    )
    assert response.status_code == 200

    response = requests.get(
        f"http://127.0.0.1/pks/lookup?op=get&search=0x{fingerprint}",
        timeout=20,
        headers={"Host": "hockeypuck.local"},
    )

    assert response.status_code == 200
    assert "BEGIN PGP PUBLIC KEY BLOCK" in response.text


@pytest.mark.dependency(depends=["test_adding_records"])
async def test_lookup_key(hockeypuck_k8s_app: Application, gpg_key: Any) -> None:
    """
    arrange: Deploy the Hockeypuck charm and create a GPG key.
    act: Execute the lookup-key action.
    assert: Action returns 0.
    """
    fingerprint = gpg_key.fingerprint
    action = await hockeypuck_k8s_app.units[0].run_action(
        "lookup-key", **{"keyword": f"0x{fingerprint}"}
    )
    await action.wait()
    assert action.results["return-code"] == 0
    assert "result" in action.results
    assert "BEGIN PGP PUBLIC KEY BLOCK" in action.results["result"]


@pytest.mark.dependency(depends=["test_adding_records"])
async def test_lookup_key_not_found(hockeypuck_k8s_app: Application) -> None:
    """
    arrange: Deploy the Hockeypuck charm.
    act: Execute the lookup-key action with an invalid key.
    assert: Action raises a 404 error
    """
    fingerprint = "RANDOMKEY"
    action = await hockeypuck_k8s_app.units[0].run_action(
        "lookup-key", **{"keyword": f"0x{fingerprint}"}
    )
    await action.wait()
    assert "Not Found" in action.results["stderr"]


@pytest.mark.usefixtures("external_peer_config")
@pytest.mark.dependency(depends=["test_adding_records"])
@pytest.mark.flaky(reruns=10, reruns_delay=10)
async def test_reconciliation(
    hockeypuck_secondary_app: Application,
    gpg_key: Any,
) -> None:
    """
    arrange: Deploy the Hockeypuck charm in the secondary model and set up peering.
    act: Reconcile the application with the first hockeypuck server.
    assert: Key is present in the secondary model hockeypuck server.
    """
    status = await hockeypuck_secondary_app.model.get_status()
    hockeypuck_secondary_application = typing.cast(
        Application, status.applications[hockeypuck_secondary_app.name]
    )
    units = hockeypuck_secondary_application.units
    for unit in units.values():
        unit_status: UnitStatus = unit
        unit_address: str = (
            unit_status.address.decode()
            if isinstance(unit_status.address, bytes)
            else typing.cast(str, unit_status.address)
        )
        response = requests.get(
            f"http://{unit_address}:{HTTP_PORT}/pks/lookup"
            f"?op=get&search=0x{gpg_key.fingerprint}",
            timeout=20,
        )

        assert response.status_code == 200, f"Key not found in {unit_address}"
        assert "BEGIN PGP PUBLIC KEY BLOCK" in response.text, "Invalid response"


@pytest.mark.dependency(depends=["test_adding_records"])
async def test_block_keys_action(hockeypuck_secondary_app: Application, gpg_key: Any) -> None:
    """
    arrange: Deploy the Hockeypuck charm in the secondary model and set up peering.
    act: Execute the delete and blocklist action.
    assert: Lookup for the key returns 404.
    """
    fingerprint = gpg_key.fingerprint
    action = await hockeypuck_secondary_app.units[0].run_action(
        "block-keys", **{"fingerprints": fingerprint, "comment": "R1234"}
    )
    await action.wait()
    assert action.results["return-code"] == 0

    status = await hockeypuck_secondary_app.model.get_status()
    hockeypuck_secondary_application = typing.cast(
        Application, status.applications[hockeypuck_secondary_app.name]
    )
    for unit in hockeypuck_secondary_application.units.values():
        unit_status: UnitStatus = unit
        unit_address: str = (
            unit_status.address.decode()
            if isinstance(unit_status.address, bytes)
            else typing.cast(str, unit_status.address)
        )
        response = requests.get(
            f"http://{unit_address}:{HTTP_PORT}/pks/lookup"
            f"?op=get&search=0x{gpg_key.fingerprint}",
            timeout=20,
        )

        assert response.status_code == 404


async def test_rebuild_prefix_tree_action(hockeypuck_k8s_app: Application) -> None:
    """
    arrange: Deploy the Hockeypuck charm and integrate with Postgres and Nginx.
    act: Execute the rebuild prefix tree action.
    assert: Action returns 0.
    """
    action = await hockeypuck_k8s_app.units[0].run_action("rebuild-prefix-tree")
    await action.wait()
    assert action.results["return-code"] == 0


async def test_traefik_integration(traefik_integration: Application) -> None:
    """
    arrange: Deploy the traefik-k8s charm and integrate with Hockeypuck.
    act: Test connectivity to the reconciliation port.
    assert: Connection request is successful.
    """
    action = await traefik_integration.units[0].run_action("show-proxied-endpoints")
    await action.wait()
    assert action.results["return-code"] == 0
    result = json.loads(action.results["proxied-endpoints"])
    host = result["traefik-k8s"]["url"].removeprefix("http://")
    port = RECONCILIATION_PORT
    try:
        with socket.create_connection((host, port), timeout=5):
            connected = True
    except (socket.timeout, socket.error):
        connected = False
    assert connected, f"Failed to connect to {host}:{port}"
