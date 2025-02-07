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


@pytest_asyncio.fixture(scope="module", name="secondary_model_alias")
async def secondary_model_fixture(ops_test: OpsTest) -> str:
    """Create a secondary Juju model for external peer reconcilitation."""
    model_alias = "secondary-model"
    model_name = "hockeypuck-secondary"
    await ops_test.track_model(model_alias, model_name=model_name)
    return model_alias


@pytest_asyncio.fixture(scope="module", name="postgresql_app")
async def postgresql_app_fixture(
    model: Model,
) -> Application:
    """Deploy postgresql-k8s charm."""
    app = await model.deploy("postgresql-k8s", channel="14/stable", trust=True)
    return app


@pytest_asyncio.fixture(scope="module", name="nginx_app")
async def nginx_app_fixture(
    model: Model,
) -> Application:
    """Deploy nginx charm."""
    config = {"service-hostname": "hockeypuck.local", "path-routes": "/"}
    app = await model.deploy(
        "nginx-ingress-integrator",
        channel="latest/edge",
        revision=99,
        trust=True,
        config=config,
    )
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
    await model.add_relation(app.name, postgresql_app.name)
    await model.add_relation(app.name, nginx_app.name)
    await model.wait_for_idle(status="active")
    return app


@pytest_asyncio.fixture(scope="module", name="gpg_key")
def gpg_key_fixture() -> Any:
    """Return a GPG key."""
    gpg = gnupg.GPG()
    input_data = gpg.gen_key_input(
        name_real="Test User", name_email="test@gmail.com", passphrase="foo"  # nosec
    )
    key = gpg.gen_key(input_data)
    return key


@pytest_asyncio.fixture(scope="module", name="hockeypuck_secondary_app")
async def hockeypuck_secondary_app_fixture(
    secondary_model_alias: str,
    hockeypuck_charm: str | Path,
    hockeypuck_app_image: str,
    ops_test: OpsTest,
) -> Application:
    """Deploy the hockeypuck-k8s application in the secondary model and relate with Postgresql"""
    resources = {
        "app-image": hockeypuck_app_image,
    }
    # Switch context to the new model
    with ops_test.model_context(secondary_model_alias) as secondary_model:
        app = await secondary_model.deploy(
            f"./{hockeypuck_charm}",
            resources=resources,
            config={
                "app-port": 11371,
                "metrics-port": 9626,
            },
        )
        postgresql_app = await secondary_model.deploy(
            "postgresql-k8s", channel="14/stable", trust=True
        )
        await secondary_model.add_relation(app.name, postgresql_app.name)
        await secondary_model.wait_for_idle(status="active")
        return app


@pytest_asyncio.fixture(scope="module", name="external_peer_config")
async def external_peer_config_fixture(
    hockeypuck_k8s_app: Application,
    hockeypuck_secondary_app: Application,
) -> None:
    """Set external peers on both hockeypuck servers for peer reconciliation."""
    # <unit-name>.<app-name>-endpoints.<model-name>.svc.cluster.local
    primary_unit_name = (hockeypuck_k8s_app.units[0].name).replace("/", "-")
    hockeypuck_primary_fqdn = (
        f"{primary_unit_name}."
        f"{hockeypuck_k8s_app.name}-endpoints."
        f"{hockeypuck_k8s_app.model.name}.svc.cluster.local"
    )
    await hockeypuck_secondary_app.set_config({"external-peers": hockeypuck_primary_fqdn})

    secondary_unit_name = (hockeypuck_secondary_app.units[0].name).replace("/", "-")
    hockeypuck_secondary_fqdn = (
        f"{secondary_unit_name}."
        f"{hockeypuck_secondary_app.name}-endpoints."
        f"{hockeypuck_secondary_app.model.name}.svc.cluster.local"
    )
    await hockeypuck_k8s_app.set_config({"external-peers": hockeypuck_secondary_fqdn})

    await hockeypuck_k8s_app.model.wait_for_idle(status="active")
    await hockeypuck_secondary_app.model.wait_for_idle(status="active")
