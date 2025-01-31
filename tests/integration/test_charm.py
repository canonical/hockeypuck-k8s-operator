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
    for unit in hockeypuck_k8s_app.units:

        url = f"http://{unit.address}:11371"
        res = requests.get(
            url,
            timeout=120,
        )
        assert res.status_code == 200
        assert b"<title>OpenPGP Keyserver</title>" in res.content
