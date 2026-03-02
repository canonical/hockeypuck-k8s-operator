# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for hockeypuck-k8s tests."""

import json
import logging
import os
import secrets
import sys
from typing import Any, Generator

import gnupg
import jubilant
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
# pylint: disable=wrong-import-position
from actions import HTTP_PORT, METRICS_PORT, RECONCILIATION_PORT  # noqa: E402
from admin_gpg import PASSWORD_ALPHABET  # noqa: E402

# pylint: enable=wrong-import-position

logger = logging.getLogger(__name__)

# renovate: depName="postgresql-k8s"
POSTGRESQL_K8S_REVISION = 774
# renovate: depName="traefik-k8s"
TRAEFIK_K8S_REVISION = 273

HOCKEYPUCK_APP_NAME = "hockeypuck-k8s"
POSTGRESQL_APP_NAME = "postgresql-k8s"
TRAEFIK_APP_NAME = "traefik-k8s"


@pytest.fixture(scope="session", name="juju")
def juju_fixture(pytestconfig) -> Generator[jubilant.Juju, None, None]:
    """Provide a Juju instance for the test session."""
    keep = pytestconfig.getoption("--keep-models")
    use_existing = pytestconfig.getoption("--use-existing")
    model = pytestconfig.getoption("--model")
    if use_existing:
        yield jubilant.Juju(model=model)
    else:
        with jubilant.temp_model(keep=keep) as juju:
            yield juju


@pytest.fixture(scope="module", name="charm")
def charm_fixture(pytestconfig) -> str:
    """Get value from parameter charm-file."""
    charm = pytestconfig.getoption("--charm-file")
    assert charm, "--charm-file must be set"
    return charm


@pytest.fixture(scope="module", name="hockeypuck_app_image")
def hockeypuck_app_image_fixture(pytestconfig) -> str:
    """Get value from parameter hockeypuck-image."""
    image = pytestconfig.getoption("--hockeypuck-image")
    assert image, "--hockeypuck-image must be set"
    return image


@pytest.fixture(scope="module", name="postgresql_app")
def postgresql_app_fixture(juju: jubilant.Juju) -> str:
    """Deploy postgresql-k8s charm."""
    juju.deploy(
        POSTGRESQL_APP_NAME,
        channel="14/edge",
        revision=POSTGRESQL_K8S_REVISION,
        trust=True,
    )
    juju.wait(lambda s: jubilant.all_active(s, POSTGRESQL_APP_NAME))
    return POSTGRESQL_APP_NAME


@pytest.fixture(scope="module", name="traefik_app")
def traefik_app_fixture(juju: jubilant.Juju) -> str:
    """Deploy traefik-k8s charm."""
    juju.deploy(
        TRAEFIK_APP_NAME,
        channel="latest/edge",
        revision=TRAEFIK_K8S_REVISION,
        trust=True,
    )
    juju.wait(lambda s: jubilant.all_active(s, TRAEFIK_APP_NAME))
    return TRAEFIK_APP_NAME


@pytest.fixture(scope="module", name="hockeypuck_k8s_app")
def hockeypuck_k8s_app_fixture(
    juju: jubilant.Juju,
    charm: str,
    hockeypuck_app_image: str,
    postgresql_app: str,
    traefik_app: str,
) -> str:
    """Deploy the hockeypuck-k8s application, relate with PostgreSQL and Traefik."""
    juju.deploy(
        charm,
        app=HOCKEYPUCK_APP_NAME,
        resources={"app-image": hockeypuck_app_image},
        config={
            "app-port": HTTP_PORT,
            "metrics-port": METRICS_PORT,
        },
    )
    juju.integrate(HOCKEYPUCK_APP_NAME, postgresql_app)
    juju.integrate(HOCKEYPUCK_APP_NAME, f"{traefik_app}:ingress")
    juju.integrate(HOCKEYPUCK_APP_NAME, f"{traefik_app}:traefik-route")
    juju.wait(jubilant.all_active)
    return HOCKEYPUCK_APP_NAME


@pytest.fixture(scope="module", name="hockeypuck_url")
def hockeypuck_url_fixture(  # pylint: disable=unused-argument
    juju: jubilant.Juju, hockeypuck_k8s_app: str
) -> str:
    """Get the endpoint proxied by Traefik."""
    task = juju.run(f"{TRAEFIK_APP_NAME}/0", "show-proxied-endpoints")
    result = json.loads(task.results["proxied-endpoints"])
    return result[HOCKEYPUCK_APP_NAME]["url"]


@pytest.fixture(scope="module", name="gpg_key")
def gpg_key_fixture() -> Any:
    """Return a GPG key."""
    gpg = gnupg.GPG()
    password = "".join(secrets.choice(PASSWORD_ALPHABET) for _ in range(10))
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


@pytest.fixture(scope="module", name="secondary_juju")
def secondary_juju_fixture(juju: jubilant.Juju) -> Generator[jubilant.Juju, None, None]:
    """Create a secondary Juju model for external peer reconciliation."""
    juju.cli("add-model", "hockeypuck-secondary")
    secondary = jubilant.Juju(model="hockeypuck-secondary")
    try:
        yield secondary
    finally:
        juju.cli("destroy-model", "hockeypuck-secondary", "--yes", "--force", "--no-wait")


@pytest.fixture(scope="module", name="hockeypuck_secondary_app")
def hockeypuck_secondary_app_fixture(
    secondary_juju: jubilant.Juju,
    charm: str,
    hockeypuck_app_image: str,
) -> str:
    """Deploy hockeypuck-k8s in the secondary model and relate with PostgreSQL."""
    secondary_juju.deploy(
        POSTGRESQL_APP_NAME,
        channel="14/edge",
        revision=POSTGRESQL_K8S_REVISION,
        trust=True,
    )
    secondary_juju.wait(lambda s: jubilant.all_active(s, POSTGRESQL_APP_NAME))
    secondary_juju.deploy(
        charm,
        app=HOCKEYPUCK_APP_NAME,
        resources={"app-image": hockeypuck_app_image},
        config={
            "app-port": HTTP_PORT,
            "metrics-port": METRICS_PORT,
        },
    )
    secondary_juju.integrate(HOCKEYPUCK_APP_NAME, POSTGRESQL_APP_NAME)
    secondary_juju.wait(jubilant.all_active)
    return HOCKEYPUCK_APP_NAME


@pytest.fixture(scope="module", name="external_peer_config")
def external_peer_config_fixture(  # pylint: disable=unused-argument
    juju: jubilant.Juju,
    secondary_juju: jubilant.Juju,
    hockeypuck_k8s_app: str,
    hockeypuck_secondary_app: str,
) -> None:
    """Set external peers on both hockeypuck servers for peer reconciliation."""
    status = juju.status()
    primary_unit_name = next(iter(status.apps[HOCKEYPUCK_APP_NAME].units))
    pod_name = primary_unit_name.replace("/", "-")
    primary_fqdn = (
        f"{pod_name}.{HOCKEYPUCK_APP_NAME}-endpoints.{status.model.name}.svc.cluster.local"
    )
    primary_config = f"{primary_fqdn},{HTTP_PORT},{RECONCILIATION_PORT}"
    secondary_juju.config(HOCKEYPUCK_APP_NAME, {"external-peers": primary_config})

    secondary_status = secondary_juju.status()
    secondary_unit_name = next(iter(secondary_status.apps[HOCKEYPUCK_APP_NAME].units))
    secondary_pod_name = secondary_unit_name.replace("/", "-")
    secondary_fqdn = (
        f"{secondary_pod_name}.{HOCKEYPUCK_APP_NAME}-endpoints."
        f"{secondary_status.model.name}.svc.cluster.local"
    )
    secondary_config = f"{secondary_fqdn},{HTTP_PORT},{RECONCILIATION_PORT}"
    juju.config(HOCKEYPUCK_APP_NAME, {"external-peers": secondary_config})

    juju.wait(jubilant.all_active)
    secondary_juju.wait(jubilant.all_active)
