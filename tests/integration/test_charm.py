#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests."""

import asyncio
import logging
from pathlib import Path

import pytest
import yaml
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


@pytest.mark.skip(reason="Will enable again while raising PR for integration tests")
async def test_build_and_deploy(ops_test: OpsTest, pytestconfig: pytest.Config):
    """Deploy the charm together with related charms.

    Assert on the unit status before any relations/configurations take place.
    """
    # Deploy the charm and wait for active/idle status
    metadata = yaml.safe_load(Path("./metadata.yaml").read_text(encoding="utf-8"))
    app_name = metadata["name"]
    charm = pytestconfig.getoption("--charm-file")
    resources = {"httpbin-image": metadata["resources"]["httpbin-image"]["upstream-source"]}
    assert ops_test.model
    await asyncio.gather(
        ops_test.model.deploy(
            f"./{charm}", resources=resources, application_name=app_name, series="jammy"
        ),
        ops_test.model.wait_for_idle(
            apps=[app_name], status="active", raise_on_blocked=True, timeout=1000
        ),
    )
