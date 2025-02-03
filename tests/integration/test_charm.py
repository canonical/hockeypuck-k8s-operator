#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests."""

import logging

import pytest
import requests

logger = logging.getLogger(__name__)


@pytest.mark.abort_on_fail
@pytest.mark.usefixtures("hockeypuck_k8s_app")
async def test_hockeypuck_health() -> None:
    """
    arrange: Build and deploy the Hockeypuck charm.
    act: Do a get request to the main page.
    assert: Returns 200 and the page contains the correct data.
    """
    response = requests.get(
        "http://127.0.0.1/",
        timeout=5,
        headers={"Host": "hockeypuck.local"},
    )
    assert response.status_code == 200
    assert "<title>OpenPGP Keyserver</title>" in response.text
