# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for the unit tests."""

import pathlib
import typing

import pytest
import yaml
from ops import testing

import charm

CHARMCRAFT_YAML = pathlib.Path(__file__).parents[2] / "charmcraft.yaml"


def _charm_metadata() -> dict[str, typing.Any]:
    """Build the metadata of the packed charm.

    The go-framework extension adds endpoints to charmcraft.yaml when the charm is packed.

    Returns:
        The charm metadata.
    """
    raw = yaml.safe_load(CHARMCRAFT_YAML.read_text(encoding="utf-8"))
    return {
        "name": raw["name"],
        "containers": {"app": {"resource": "app-image"}},
        "resources": {"app-image": {"type": "oci-image"}},
        "peers": raw["peers"],
        "provides": {
            "metrics-endpoint": {"interface": "prometheus_scrape"},
            "grafana-dashboard": {"interface": "grafana_dashboard"},
        },
        "requires": {
            **raw["requires"],
            "logging": {"interface": "loki_push_api"},
            "ingress": {"interface": "ingress", "limit": 1},
        },
    }


@pytest.fixture(name="context")
def context_fixture() -> testing.Context:
    """Create a testing context for the Hockeypuck charm.

    Returns:
        The testing context.
    """
    raw = yaml.safe_load(CHARMCRAFT_YAML.read_text(encoding="utf-8"))
    # charmcraft.yaml calls the action parameters "properties".
    actions = {
        name: {"params": action.get("properties", {}), "required": action.get("required", [])}
        for name, action in raw["actions"].items()
    }
    actions["rotate-secret-key"] = {}
    config = {
        "options": {**raw["config"]["options"], "app-secret-key": {"type": "secret"}},
    }
    return testing.Context(
        charm.HockeypuckK8SCharm, meta=_charm_metadata(), actions=actions, config=config
    )
