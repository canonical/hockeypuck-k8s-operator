#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests."""

import json
import logging
import socket
from typing import Any

import jubilant
import pytest
import requests
from gnupg import GPG

from actions import HTTP_PORT, RECONCILIATION_PORT
from tests.integration.conftest import APP_NAME, TRAEFIK_APP_NAME

logger = logging.getLogger(__name__)


@pytest.mark.usefixtures("hockeypuck_k8s_app")
def test_hockeypuck_health(hockeypuck_url: str) -> None:
    """
    arrange: Build and deploy the Hockeypuck charm.
    act: Send a request to the main page.
    assert: Returns 200 and the page contains the title.
    """
    response = requests.get(
        f"{hockeypuck_url}/",
        timeout=5,
    )
    assert response.status_code == 200
    assert "<title>OpenPGP Keyserver</title>" in response.text


@pytest.mark.usefixtures("hockeypuck_k8s_app")
@pytest.mark.dependency(name="test_adding_records")
def test_adding_records(gpg_key: Any, hockeypuck_url: str) -> None:
    """
    arrange: Create a GPG Key
    act: Send a request to add a PGP key and lookup the key using the API
    assert: API is added successfully and lookup of key returns the key.
    """
    gpg = GPG()
    fingerprint = gpg_key.fingerprint
    public_key = gpg.export_keys(fingerprint)
    response = requests.post(
        f"{hockeypuck_url}/pks/add",
        timeout=20,
        data={"keytext": public_key},
    )
    assert response.status_code == 200

    response = requests.get(
        f"{hockeypuck_url}/pks/lookup?op=get&search=0x{fingerprint}",
        timeout=20,
        headers={"Host": "hockeypuck.local"},
    )

    assert response.status_code == 200
    assert "BEGIN PGP PUBLIC KEY BLOCK" in response.text


@pytest.mark.dependency(depends=["test_adding_records"])
def test_lookup_key(juju: jubilant.Juju, hockeypuck_k8s_app: str, gpg_key: Any) -> None:
    """
    arrange: Deploy the Hockeypuck charm and create a GPG key.
    act: Execute the lookup-key action.
    assert: Action returns 0.
    """
    fingerprint = gpg_key.fingerprint
    task = juju.run(f"{hockeypuck_k8s_app}/0", "lookup-key", {"keyword": f"0x{fingerprint}"})
    assert task.return_code == 0
    assert "result" in task.results
    assert "BEGIN PGP PUBLIC KEY BLOCK" in task.results["result"]


def test_lookup_key_not_found(juju: jubilant.Juju, hockeypuck_k8s_app: str) -> None:
    """
    arrange: Deploy the Hockeypuck charm.
    act: Execute the lookup-key action with an invalid key.
    assert: Action raises a 404 error
    """
    fingerprint = "RANDOMKEY"
    with pytest.raises(jubilant.TaskError) as exc_info:
        juju.run(f"{hockeypuck_k8s_app}/0", "lookup-key", {"keyword": f"0x{fingerprint}"})
    assert "Not Found" in exc_info.value.task.message


def test_unit_limit(juju: jubilant.Juju, hockeypuck_k8s_app: str) -> None:
    """
    arrange: Deploy the Hockeypuck charm.
    act: Add a unit to the application.
    assert: The application is blocked.
    """
    juju.add_unit(hockeypuck_k8s_app)
    juju.wait(lambda s: jubilant.all_blocked(s, hockeypuck_k8s_app))
    status = juju.status()
    assert status.apps[hockeypuck_k8s_app].app_status.current == "blocked"
    assert (
        status.apps[hockeypuck_k8s_app].app_status.message
        == "Hockeypuck does not support multi-unit deployments"
    )
    juju.remove_unit(hockeypuck_k8s_app, num_units=1)
    juju.wait(lambda s: jubilant.all_active(s, hockeypuck_k8s_app))
    assert juju.status().apps[hockeypuck_k8s_app].app_status.current == "active"


@pytest.mark.usefixtures("external_peer_config")
@pytest.mark.dependency(depends=["test_adding_records"])
@pytest.mark.flaky(reruns=10, reruns_delay=10)
def test_reconciliation(
    juju_secondary: jubilant.Juju,
    hockeypuck_secondary_app: str,
    gpg_key: Any,
) -> None:
    """
    arrange: Deploy the Hockeypuck charm in the secondary model and set up peering.
    act: Reconcile the application with the first hockeypuck server.
    assert: Key is present in the secondary model hockeypuck server.
    """
    status = juju_secondary.status()
    for _unit_name, unit_info in status.get_units(hockeypuck_secondary_app).items():
        unit_address = unit_info.address
        response = requests.get(
            f"http://{unit_address}:{HTTP_PORT}/pks/lookup"
            f"?op=get&search=0x{gpg_key.fingerprint}",
            timeout=20,
        )

        assert response.status_code == 200, f"Key not found in {unit_address}"
        assert "BEGIN PGP PUBLIC KEY BLOCK" in response.text, "Invalid response"


@pytest.mark.dependency(depends=["test_adding_records"])
def test_block_keys_action(
    juju_secondary: jubilant.Juju, hockeypuck_secondary_app: str, gpg_key: Any
) -> None:
    """
    arrange: Deploy the Hockeypuck charm in the secondary model and set up peering.
    act: Execute the delete and blocklist action.
    assert: Lookup for the key returns 404.
    """
    fingerprint = gpg_key.fingerprint
    task = juju_secondary.run(
        f"{hockeypuck_secondary_app}/0",
        "block-keys",
        {"fingerprints": fingerprint, "comment": "R1234"},
    )
    assert task.return_code == 0

    status = juju_secondary.status()
    for _unit_name, unit_info in status.get_units(hockeypuck_secondary_app).items():
        unit_address = unit_info.address
        response = requests.get(
            f"http://{unit_address}:{HTTP_PORT}/pks/lookup"
            f"?op=get&search=0x{gpg_key.fingerprint}",
            timeout=20,
        )

        assert response.status_code == 404


@pytest.mark.dependency(depends=["test_adding_records"])
def test_block_keys_action_multiple(
    juju: jubilant.Juju, hockeypuck_k8s_app: str, gpg_key: Any
) -> None:
    """
    arrange: Deploy the Hockeypuck charm.
    act: Execute the delete and blocklist action with multiple keys (one valid and present,
    one invalid, one valid but not present).
    assert: Action returns 0 and event result contains the status of each key.
    """
    fingerprint1 = str(gpg_key.fingerprint).lower()  # valid key that is present in the database
    fingerprint2 = "eaf2dd785260ec0cd047f463e449a664b36b34b1"  # valid key that is not present
    fingerprint3 = "shbfsdiuf98hu"  # invalid key
    task = juju.run(
        f"{hockeypuck_k8s_app}/0",
        "block-keys",
        {"fingerprints": f"{fingerprint1},{fingerprint2},{fingerprint3}", "comment": "R1234"},
    )
    expected_result = {}
    expected_result[fingerprint1] = "Deleted and blocked successfully."
    expected_result[fingerprint2] = "Fingerprint unavailable in the database."
    expected_result[fingerprint3] = (
        "Invalid fingerprint format. "
        "Fingerprints must be 40 or 64 characters long and "
        "consist of hexadecimal characters only."
    )
    assert task.results[fingerprint1] == expected_result[fingerprint1]
    assert task.results[fingerprint2] == expected_result[fingerprint2]
    assert task.results[fingerprint3] == expected_result[fingerprint3]


def test_rebuild_prefix_tree_action(juju: jubilant.Juju, hockeypuck_k8s_app: str) -> None:
    """
    arrange: Deploy the Hockeypuck charm and integrate with Postgres and Traefik.
    act: Execute the rebuild prefix tree action.
    assert: Action returns 0.
    """
    task = juju.run(f"{hockeypuck_k8s_app}/0", "rebuild-prefix-tree")
    assert task.return_code == 0


def test_traefik_route_integration(juju: jubilant.Juju, traefik_app: str) -> None:
    """
    arrange: Deploy the traefik-k8s charm and integrate with Hockeypuck.
    act: Test connectivity to the reconciliation port.
    assert: Connection request is successful.
    """
    task = juju.run(f"{TRAEFIK_APP_NAME}/0", "show-proxied-endpoints")
    assert task.return_code == 0
    result = json.loads(task.results["proxied-endpoints"])
    host = result[TRAEFIK_APP_NAME]["url"].removeprefix("http://")
    port = RECONCILIATION_PORT
    try:
        with socket.create_connection((host, port), timeout=5):
            connected = True
    except (socket.timeout, socket.error):
        connected = False
    assert connected, f"Failed to connect to {host}:{port}"
