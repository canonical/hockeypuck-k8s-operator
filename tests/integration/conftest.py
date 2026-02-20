# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for hockeypuck-k8s tests."""

import json
import logging
from collections.abc import Generator
from pathlib import Path
from typing import Any, cast

import gnupg
import jubilant
import pytest
from passlib.pwd import genword
from pytest import Config

from actions import HTTP_PORT, METRICS_PORT, RECONCILIATION_PORT

logger = logging.getLogger(__name__)

# renovate: depName="postgresql-k8s"
POSTGRESQL_REVISION = 450
# renovate: depName="traefik-k8s"
TRAEFIK_REVISION = 247


@pytest.fixture(scope="session", name="juju")
def juju_fixture(request: pytest.FixtureRequest) -> Generator[jubilant.Juju, None, None]:
    """Pytest fixture that wraps :meth:`jubilant.with_model`."""

    def show_debug_log(juju: jubilant.Juju):
        """Show debug log.

        Args:
            juju: the Juju object.
        """
        if request.session.testsfailed:
            log = juju.debug_log(limit=1000)
            print(log, end="")

    use_existing = request.config.getoption("--use-existing", default=False)
    if use_existing:
        juju = jubilant.Juju()
        yield juju
        show_debug_log(juju)
        return

    model = request.config.getoption("--model")
    if model:
        juju = jubilant.Juju(model=model)
        yield juju
        show_debug_log(juju)
        return

    keep_models = cast(bool, request.config.getoption("--keep-models"))
    with jubilant.temp_model(keep=keep_models) as juju:
        juju.wait_timeout = 10 * 60
        yield juju
        show_debug_log(juju)
        return


@pytest.fixture(scope="module", name="secondary_juju")
def secondary_juju_fixture(
    request: pytest.FixtureRequest,
) -> Generator[jubilant.Juju, None, None]:
    """Create a secondary Juju model for external peer reconciliation."""

    def show_debug_log(juju: jubilant.Juju):
        """Show debug log.

        Args:
            juju: the Juju object.
        """
        if request.session.testsfailed:
            log = juju.debug_log(limit=1000)
            print(log, end="")

    model_name = "hockeypuck-secondary"
    keep_models = cast(bool, request.config.getoption("--keep-models"))

    # Create a Juju instance and add the model manually
    juju = jubilant.Juju()
    juju.add_model(model_name)
    juju_secondary = jubilant.Juju(model=model_name)
    juju_secondary.wait_timeout = 10 * 60

    try:
        yield juju_secondary
        show_debug_log(juju_secondary)
    finally:
        if not keep_models:
            juju.destroy_model(model_name)


@pytest.fixture(scope="module", name="postgresql_app")
def postgresql_app_fixture(
    juju: jubilant.Juju,
) -> str:
    """Deploy postgresql-k8s charm."""
    app_name = "postgresql-k8s"
    if juju.status().apps.get(app_name):
        logger.info("%s already deployed", app_name)
        return app_name

    juju.deploy(
        app_name,
        channel="14/edge",
        revision=POSTGRESQL_REVISION,
        trust=True,
    )
    juju.wait(lambda status: status.apps[app_name].is_active, timeout=10 * 60)
    return app_name


@pytest.fixture(scope="module", name="traefik_app")
def traefik_app_fixture(
    juju: jubilant.Juju,
) -> str:
    """Deploy traefik-k8s charm."""
    app_name = "traefik-k8s"
    if juju.status().apps.get(app_name):
        logger.info("%s already deployed", app_name)
        return app_name

    juju.deploy(
        app_name,
        channel="latest/edge",
        revision=TRAEFIK_REVISION,
        trust=True,
    )
    juju.wait(lambda status: status.apps[app_name].is_active, timeout=10 * 60)
    return app_name


@pytest.fixture(scope="module", name="hockeypuck_url")
def hockeypuck_url_fixture(
    juju: jubilant.Juju,
    traefik_app: str,
) -> str:
    """Get the endpoint proxied by Traefik."""
    result = juju.run(f"{traefik_app}/0", "show-proxied-endpoints", wait=True)
    proxied_endpoints = json.loads(result.results.get("proxied-endpoints", "{}"))
    hockeypuck_url = proxied_endpoints["hockeypuck-k8s"]["url"]
    return hockeypuck_url


@pytest.fixture(scope="module", name="hockeypuck_charm")
def hockeypuck_charm_fixture(pytestconfig: Config) -> str | Path:
    """Get value from parameter charm-file."""
    charm = pytestconfig.getoption("--charm-file")
    use_existing = pytestconfig.getoption("--use-existing", default=False)
    if not use_existing:
        assert charm, "--charm-file must be set"
    return charm if charm else ""


@pytest.fixture(scope="module", name="hockeypuck_app_image")
def hockeypuck_app_image_fixture(pytestconfig: Config) -> str:
    """Get value from parameter rock-file."""
    rock = pytestconfig.getoption("--hockeypuck-image")
    assert rock, "--hockeypuck-image must be set"
    return rock


@pytest.fixture(scope="module", name="hockeypuck_k8s_app")
def hockeypuck_k8s_app_fixture(
    juju: jubilant.Juju,
    hockeypuck_charm: str | Path,
    hockeypuck_app_image: str,
    traefik_app: str,
    postgresql_app: str,
) -> str:
    """Deploy the hockeypuck-k8s application, relates with Postgresql and Traefik."""
    app_name = "hockeypuck-k8s"
    if juju.status().apps.get(app_name):
        logger.info("%s already deployed", app_name)
        return app_name

    resources = {
        "app-image": hockeypuck_app_image,
    }
    juju.deploy(
        str(hockeypuck_charm),
        app=app_name,
        resources=resources,
        config={
            "app-port": HTTP_PORT,
            "metrics-port": METRICS_PORT,
        },
    )
    juju.integrate(app_name, postgresql_app)
    juju.integrate(app_name, f"{traefik_app}:ingress")
    juju.integrate(app_name, f"{traefik_app}:traefik-route")
    juju.wait(jubilant.all_active, timeout=15 * 60)
    return app_name


@pytest.fixture(scope="module", name="gpg_key")
def gpg_key_fixture() -> Any:
    """Return a GPG key."""
    gpg = gnupg.GPG()
    password = genword(length=10)
    input_data = gpg.gen_key_input(
        key_type="RSA",
        key_length=2048,
        name_real="Test User",
        name_email="test@gmail.com",
        passphrase=password,
    )
    key = gpg.gen_key(input_data)
    if not key.fingerprint:
        raise RuntimeError("GPG key generation failed.")
    return key


@pytest.fixture(scope="module", name="hockeypuck_secondary_app")
def hockeypuck_secondary_app_fixture(
    secondary_juju: jubilant.Juju,
    hockeypuck_charm: str | Path,
    hockeypuck_app_image: str,
) -> str:
    """Deploy the hockeypuck-k8s application in the secondary model and relate with Postgresql"""
    app_name = "hockeypuck-k8s"
    if secondary_juju.status().apps.get(app_name):
        logger.info("%s already deployed in secondary model", app_name)
        return app_name

    resources = {
        "app-image": hockeypuck_app_image,
    }
    secondary_juju.deploy(
        str(hockeypuck_charm),
        app=app_name,
        resources=resources,
        config={
            "app-port": HTTP_PORT,
            "metrics-port": METRICS_PORT,
        },
    )
    secondary_juju.deploy(
        "postgresql-k8s",
        channel="14/edge",
        revision=POSTGRESQL_REVISION,
        trust=True,
    )
    secondary_juju.wait(lambda status: status.apps["postgresql-k8s"].is_active, timeout=10 * 60)
    secondary_juju.integrate(app_name, "postgresql-k8s")
    secondary_juju.wait(jubilant.all_active, timeout=15 * 60)
    return app_name


@pytest.fixture(scope="module", name="external_peer_config")
def external_peer_config_fixture(
    juju: jubilant.Juju,
    secondary_juju: jubilant.Juju,
    hockeypuck_k8s_app: str,
    hockeypuck_secondary_app: str,
) -> None:
    """Set external peers on both hockeypuck servers for peer reconciliation."""
    # <unit-name>.<app-name>-endpoints.<model-name>.svc.cluster.local
    primary_status = juju.status()
    primary_model_name = primary_status.model.name
    primary_unit_name = f"{hockeypuck_k8s_app}-0".replace("/", "-")
    hockeypuck_primary_fqdn = (
        f"{primary_unit_name}."
        f"{hockeypuck_k8s_app}-endpoints."
        f"{primary_model_name}.svc.cluster.local"
    )
    primary_config = f"{hockeypuck_primary_fqdn},{HTTP_PORT},{RECONCILIATION_PORT}"
    secondary_juju.config(hockeypuck_secondary_app, {"external-peers": primary_config})

    secondary_status = secondary_juju.status()
    secondary_model_name = secondary_status.model.name
    secondary_unit_name = f"{hockeypuck_secondary_app}-0".replace("/", "-")
    hockeypuck_secondary_fqdn = (
        f"{secondary_unit_name}."
        f"{hockeypuck_secondary_app}-endpoints."
        f"{secondary_model_name}.svc.cluster.local"
    )
    secondary_config = f"{hockeypuck_secondary_fqdn},{HTTP_PORT},{RECONCILIATION_PORT}"
    juju.config(hockeypuck_k8s_app, {"external-peers": secondary_config})

    juju.wait(jubilant.all_active, timeout=10 * 60)
    secondary_juju.wait(jubilant.all_active, timeout=10 * 60)
