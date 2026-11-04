# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit tests for the reconciliation route."""

import ops
import pytest
import yaml
from ops import testing

import reconciliation_route
from actions import RECONCILIATION_PORT

META = {
    "name": "hockeypuck",
    "requires": {reconciliation_route.RELATION_NAME: {"interface": "traefik_route"}},
}


class RouteCharm(ops.CharmBase):
    """Charm publishing the reconciliation route."""

    def __init__(self, framework: ops.Framework):
        """Construct.

        Args:
            framework: The ops framework.
        """
        super().__init__(framework)
        self.route = reconciliation_route.ReconciliationRouteRelation(self)
        self.route.setup(on_change=lambda: None)


@pytest.fixture(name="context")
def context_fixture() -> testing.Context:
    """Create a testing context for the route charm.

    Returns:
        The testing context.
    """
    return testing.Context(RouteCharm, meta=META)


@pytest.fixture(autouse=True)
def fqdn_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make the unit FQDN deterministic.

    Args:
        monkeypatch: The pytest monkeypatch fixture.
    """
    monkeypatch.setattr(reconciliation_route.socket, "getfqdn", lambda: "hockeypuck.local")


def test_route_published(context):
    """
    arrange: a unit integrated with traefik.
    act: run the relation-changed event.
    assert: the TCP route and the static entrypoint are published.
    """
    relation = testing.Relation(reconciliation_route.RELATION_NAME)
    state = testing.State(leader=True, relations=[relation])

    state_out = context.run(context.on.relation_changed(relation), state)

    databag = state_out.get_relation(relation.id).local_app_data
    config = yaml.safe_load(databag["config"])
    assert config["tcp"]["routers"] == reconciliation_route.HOCKEYPUCK_TCP_ROUTER
    assert config["tcp"]["services"]["hockeypuck-tcp-service"] == {
        "loadBalancer": {"servers": [{"address": f"hockeypuck.local:{RECONCILIATION_PORT}"}]}
    }
    assert yaml.safe_load(databag["static"]) == {
        "entryPoints": {"reconciliation-port": {"address": f":{RECONCILIATION_PORT}"}}
    }
