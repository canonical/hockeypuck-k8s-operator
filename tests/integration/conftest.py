# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for hockeypuck-k8s tests."""

import json
import logging
import secrets
import shlex
import subprocess  # nosec B404
from pathlib import Path
from typing import Any

import gnupg
import jubilant
import pytest
from pytest import Config

from actions import HTTP_PORT, METRICS_PORT, RECONCILIATION_PORT
from admin_gpg import PASSWORD_ALPHABET

logger = logging.getLogger(__name__)


def pack(root: Path | str = "./", platform: str | None = None) -> Path:
    """Pack a local charm with charmcraft and return the path to the .charm file.

    Args:
        root: The root directory of the charm to pack.
        platform: Optional platform to pass to charmcraft pack.

    Returns:
        The resolved path to the packed .charm file.

    Raises:
        ValueError: If no charms were packed or multiple charms were packed without
            specifying a platform.
    """
    platform_arg = f" --platform {platform}" if platform else ""
    cmd = f"charmcraft pack -p {root}{platform_arg}"
    proc = subprocess.run(  # nosec B603
        shlex.split(cmd),
        check=True,
        capture_output=True,
        text=True,
    )
    # charmcraft outputs "Packed <filename>" lines to stderr.
    packed_charms = [
        line.split()[1] for line in proc.stderr.strip().splitlines() if line.startswith("Packed")
    ]
    if not packed_charms:
        raise ValueError(
            f"unable to get packed charm(s) ({cmd!r} completed with "
            f"{proc.returncode=}, {proc.stdout=}, {proc.stderr=})"
        )
    if len(packed_charms) > 1:
        raise ValueError(
            "This charm supports multiple platforms. "
            "Pass a `platform` argument to control which charm you're getting instead."
        )
    return Path(packed_charms[0]).resolve()


APP_NAME = "hockeypuck-k8s"
POSTGRESQL_APP_NAME = "postgresql-k8s"
TRAEFIK_APP_NAME = "traefik-k8s"


@pytest.fixture(scope="module", name="hockeypuck_charm")
def hockeypuck_charm_fixture(pytestconfig: Config) -> Path:
    """Get or build the charm file."""
    charm = pytestconfig.getoption("--charm-file")
    if not charm:
        return pack(".")
    return Path(charm).resolve()


@pytest.fixture(scope="module", name="hockeypuck_app_image")
def hockeypuck_app_image_fixture(pytestconfig: Config) -> str:
    """Get value from parameter --hockeypuck-image."""
    rock = pytestconfig.getoption("--hockeypuck-image")
    assert rock, "--hockeypuck-image must be set"
    return rock


@pytest.fixture(scope="module", name="postgresql_app")
def postgresql_app_fixture(juju: jubilant.Juju) -> str:
    """Deploy postgresql-k8s charm."""
    juju.deploy(POSTGRESQL_APP_NAME, channel="14/stable", trust=True)
    juju.wait(lambda s: jubilant.all_active(s, POSTGRESQL_APP_NAME))
    return POSTGRESQL_APP_NAME


@pytest.fixture(scope="module", name="traefik_app")
def traefik_app_fixture(juju: jubilant.Juju) -> str:
    """Deploy traefik-k8s charm."""
    juju.deploy(TRAEFIK_APP_NAME, channel="latest/stable", trust=True)
    juju.wait(lambda s: jubilant.all_active(s, TRAEFIK_APP_NAME))
    return TRAEFIK_APP_NAME


@pytest.fixture(scope="module", name="hockeypuck_k8s_app")
def hockeypuck_k8s_app_fixture(
    juju: jubilant.Juju,
    hockeypuck_charm: Path,
    hockeypuck_app_image: str,
    traefik_app: str,
    postgresql_app: str,
) -> str:
    """Deploy the hockeypuck-k8s application, relates with Postgresql and Traefik."""
    resources = {"app-image": hockeypuck_app_image}
    juju.deploy(
        hockeypuck_charm,
        resources=resources,
        config={
            "app-port": HTTP_PORT,
            "metrics-port": METRICS_PORT,
        },
    )
    juju.integrate(APP_NAME, postgresql_app)
    juju.integrate(APP_NAME, f"{traefik_app}:ingress")
    juju.integrate(APP_NAME, f"{traefik_app}:traefik-route")
    juju.wait(jubilant.all_active)
    return APP_NAME


@pytest.fixture(scope="module", name="hockeypuck_url")
def hockeypuck_url_fixture(juju: jubilant.Juju, hockeypuck_k8s_app: str) -> str:
    """Get the endpoint proxied by Traefik."""
    task = juju.run(f"{TRAEFIK_APP_NAME}/0", "show-proxied-endpoints")
    proxied_endpoints = json.loads(task.results["proxied-endpoints"])
    return proxied_endpoints[hockeypuck_k8s_app]["url"]


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


@pytest.fixture(scope="module", name="juju_secondary")
def juju_secondary_fixture(temp_model_factory: Any) -> jubilant.Juju:
    """Create a secondary Juju model for external peer reconciliation."""
    return temp_model_factory.get_juju("secondary")


@pytest.fixture(scope="module", name="hockeypuck_secondary_app")
def hockeypuck_secondary_app_fixture(
    juju_secondary: jubilant.Juju,
    hockeypuck_charm: Path,
    hockeypuck_app_image: str,
) -> str:
    """Deploy the hockeypuck-k8s application in the secondary model and relate with Postgresql."""
    resources = {"app-image": hockeypuck_app_image}
    juju_secondary.deploy(
        hockeypuck_charm,
        resources=resources,
        config={
            "app-port": HTTP_PORT,
            "metrics-port": METRICS_PORT,
        },
    )
    juju_secondary.deploy(POSTGRESQL_APP_NAME, channel="14/stable", trust=True)
    juju_secondary.wait(lambda s: jubilant.all_active(s, POSTGRESQL_APP_NAME))
    juju_secondary.integrate(APP_NAME, POSTGRESQL_APP_NAME)
    juju_secondary.wait(jubilant.all_active)
    return APP_NAME


@pytest.fixture(scope="module", name="external_peer_config")
def external_peer_config_fixture(
    juju: jubilant.Juju,
    juju_secondary: jubilant.Juju,
    hockeypuck_k8s_app: str,
    hockeypuck_secondary_app: str,
) -> None:
    """Set external peers on both hockeypuck servers for peer reconciliation."""
    # <unit-name>.<app-name>-endpoints.<model-name>.svc.cluster.local
    status_primary = juju.status()
    primary_unit_name = next(iter(status_primary.get_units(hockeypuck_k8s_app))).replace("/", "-")
    primary_model_name = status_primary.model.name
    hockeypuck_primary_fqdn = (
        f"{primary_unit_name}."
        f"{hockeypuck_k8s_app}-endpoints."
        f"{primary_model_name}.svc.cluster.local"
    )
    primary_config = f"{hockeypuck_primary_fqdn},{HTTP_PORT},{RECONCILIATION_PORT}"
    juju_secondary.config(hockeypuck_secondary_app, {"external-peers": primary_config})

    status_secondary = juju_secondary.status()
    secondary_unit_name = next(iter(status_secondary.get_units(hockeypuck_secondary_app))).replace(
        "/", "-"
    )
    secondary_model_name = status_secondary.model.name
    hockeypuck_secondary_fqdn = (
        f"{secondary_unit_name}."
        f"{hockeypuck_secondary_app}-endpoints."
        f"{secondary_model_name}.svc.cluster.local"
    )
    secondary_config = f"{hockeypuck_secondary_fqdn},{HTTP_PORT},{RECONCILIATION_PORT}"
    juju.config(hockeypuck_k8s_app, {"external-peers": secondary_config})

    juju.wait(jubilant.all_active)
    juju_secondary.wait(jubilant.all_active)
