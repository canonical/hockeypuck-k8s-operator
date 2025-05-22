# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

# Learn more about testing at: https://juju.is/docs/sdk/testing

"""Unit tests for traefik route observer."""

import socket
from unittest import mock

import ops
import pytest
from ops.testing import Harness

import traefik_route_observer
from actions import RECONCILIATION_PORT

REQUIRER_METADATA = """
name: observer-charm
requires:
  traefik-route:
    interface: traefik_route
"""


class ObservedCharm(ops.CharmBase):
    """Class for requirer charm testing."""

    def __init__(self, *args):
        """Construct.

        Args:
            args: Variable list of positional arguments passed to the parent constructor.
        """
        super().__init__(*args)
        self.traefik_route = traefik_route_observer.TraefikRouteObserver(self)


def test_on_traefik_route_relation_joined_when_leader(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    arrange: instantiate a charm with leadership implementing the traefik-route relation.
    act: integrate the charm leveraging the traefik-route integration.
    assert: traefik is configured with the appropriate values.
    """
    harness = Harness(ObservedCharm, meta=REQUIRER_METADATA)
    harness.set_model_name("testing")
    harness.begin_with_initial_hooks()
    harness.set_leader(True)
    harness.add_relation(traefik_route_observer.RELATION_NAME, "traefik-route-provider")

    requirer_mock = mock.MagicMock()
    requirer_mock.is_ready.return_value = True
    requirer_mock.units = set()
    monkeypatch.setattr(harness.charm.traefik_route, "traefik_route", requirer_mock)
    monkeypatch.setattr(socket, "getfqdn", lambda: "hockeypuck.local")
    monkeypatch.setattr(harness.charm.model, "get_relation", lambda _: requirer_mock)

    harness.charm.traefik_route._configure_traefik_route()  # pylint: disable=protected-access

    requirer_mock.submit_to_traefik.assert_called_once_with(
        {
            "tcp": {
                "routers": traefik_route_observer.HOCKEYPUCK_TCP_ROUTER,
                "services": {
                    "hockeypuck-tcp-service": {
                        "loadBalancer": {
                            "servers": [{"address": f"hockeypuck.local:{RECONCILIATION_PORT}"}]
                        },
                    }
                },
            }
        },
        static={"entryPoints": {"reconciliation-port": {"address": f":{RECONCILIATION_PORT}"}}},
    )


def test_on_traefik_route_relation_joined_when_not_leader(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    arrange: instantiate a charm without leadership implementing the traefik-route relation.
    act: integrate the charm leveraging the traefik-route integration.
    assert: the traefik configuration is not changed.
    """
    harness = Harness(ObservedCharm, meta=REQUIRER_METADATA)
    harness.begin_with_initial_hooks()
    harness.set_leader(False)
    harness.add_relation(traefik_route_observer.RELATION_NAME, "traefik-route-provider")
    mock_obj = mock.Mock()
    monkeypatch.setattr(harness.charm.traefik_route.traefik_route, "submit_to_traefik", mock_obj)

    harness.charm.traefik_route._configure_traefik_route()  # pylint: disable=protected-access

    mock_obj.assert_not_called()
