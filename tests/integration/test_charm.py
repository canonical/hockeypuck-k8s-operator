#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests."""

import logging

import requests
from juju.application import Application

logger = logging.getLogger(__name__)


async def test_hockeypuck_health(hockeypuck_k8s_app: Application) -> None:
    """
    arrange: Build and deploy the Hockeypuck charm.
    act: Do a get request to the main page.
    assert: Returns 200 and the page contains the correct data.
    """
    status = await hockeypuck_k8s_app.model.get_status()
    unit_ips = [
        unit.address for unit in status.applications[hockeypuck_k8s_app.name].units.values()
    ]
    for unit_ip in unit_ips:

        url = f"http://{unit_ip}:11371"
        res = requests.get(
            url,
            timeout=120,
        )
        assert res.status_code == 200
        assert b"<title>OpenPGP Keyserver</title>" in res.content
