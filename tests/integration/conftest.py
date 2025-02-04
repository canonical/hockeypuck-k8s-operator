# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for hockeypuck-k8s tests."""

import logging
from pathlib import Path
from typing import Any

import gnupg
import pytest_asyncio
from juju.application import Application
from juju.model import Model
from pytest import Config
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


@pytest_asyncio.fixture(scope="module", name="model")
async def model_fixture(ops_test: OpsTest) -> Model:
    """Return the current testing juju model."""
    assert ops_test.model
    return ops_test.model


@pytest_asyncio.fixture(scope="module", name="postgresql_app")
async def postgresql_app_fixture(
    ops_test: OpsTest,
    model: Model,
) -> Application:
    """Deploy postgresql-k8s charm."""
    async with ops_test.fast_forward():
        app = await model.deploy("postgresql-k8s", channel="14/stable", trust=True)
        await model.wait_for_idle(apps=["postgresql-k8s"], timeout=15 * 60)
    return app


@pytest_asyncio.fixture(scope="module", name="nginx_app")
async def nginx_app_fixture(
    ops_test: OpsTest,
    model: Model,
) -> Application:
    """Deploy nginx charm."""
    config = {"service-hostname": "hockeypuck.local", "path-routes": "/"}
    async with ops_test.fast_forward():
        app = await model.deploy(
            "nginx-ingress-integrator",
            channel="latest/edge",
            revision=99,
            trust=True,
            config=config,
        )
        await model.wait_for_idle()
    return app


@pytest_asyncio.fixture(scope="module", name="hockeypuck_charm")
async def hockeypuck_charm_fixture(pytestconfig: Config, ops_test: OpsTest) -> str | Path:
    """Get value from parameter charm-file."""
    charm = pytestconfig.getoption("--charm-file")
    if not charm:
        charm = await ops_test.build_charm(".")
        assert charm, "Charm not built"
        return charm
    return charm


@pytest_asyncio.fixture(scope="module", name="hockeypuck_app_image")
async def hockeypuck_app_image_fixture(pytestconfig: Config) -> str:
    """Get value from parameter rock-file."""
    rock = pytestconfig.getoption("--hockeypuck-image")
    assert rock, "--hockeypuck-image must be set"
    return rock


@pytest_asyncio.fixture(scope="module", name="hockeypuck_k8s_app")
async def hockeypuck_k8s_app_fixture(
    model: Model,
    hockeypuck_charm: str | Path,
    hockeypuck_app_image: str,
    nginx_app: Application,
    postgresql_app: Application,
) -> Application:
    """Deploy the hockeypuck-k8s application, relates with Postgresql and Nginx."""
    resources = {
        "app-image": hockeypuck_app_image,
    }
    app = await model.deploy(
        f"./{hockeypuck_charm}",
        resources=resources,
        config={
            "app-port": 11371,
            "metrics-port": 9626,
        },
    )
    await model.wait_for_idle(apps=[app.name], timeout=3 * 60, status="blocked")
    await model.add_relation(app.name, postgresql_app.name)
    await model.add_relation(app.name, nginx_app.name)
    await model.wait_for_idle()
    return app


@pytest_asyncio.fixture(scope="function", name="gpg_key")
def gpg_key_fixture() -> Any:
    """Return a GPG key."""
    gpg = gnupg.GPG()
    input_data = gpg.gen_key_input(
        name_real="Test User", name_email="test@gmail.com", passphrase="foo"  # nosec
    )
    key = gpg.gen_key(input_data)
    return key
