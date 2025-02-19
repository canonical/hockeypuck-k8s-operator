# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Traefik route observer module."""

import socket

import ops
from charms.traefik_k8s.v0.traefik_route import TraefikRouteRequirer

RELATION_NAME = "traefik-route"


class TraefikRouteObserver(ops.Object):
    """Traefik route relation observer."""

    def __init__(self, charm: ops.CharmBase):
        """Initialize the observer and register event handlers.

        Args:
            charm: The parent charm.
        """
        super().__init__(charm, RELATION_NAME)
        self._charm = charm
        self.traefik_route = self._register_traefik_route()

    def _register_traefik_route(self) -> TraefikRouteRequirer:
        """Create a TraefikRouteRequirer instance submit traefik route configuration.

        Returns:
            The TraefikRoute instance.
        """
        traefik_route = TraefikRouteRequirer(
            self._charm, self.model.get_relation(RELATION_NAME), RELATION_NAME
        )
        if self._charm.unit.is_leader() and traefik_route.is_ready():
            traefik_route.submit_to_traefik(self._route_config, static=self._static_config)
        return traefik_route

    @property
    def _static_config(self) -> dict[str, dict[str, dict[str, str]]]:
        """Return the static configuration for the Hockeypuck service.

        Returns:
            The static configuration for traefik.
        """
        entry_points = {"reconciliation-port": {"address": ":11370"}}
        return {
            "entryPoints": entry_points,
        }

    @property
    def _route_config(self) -> dict[str, dict[str, object]]:
        """Return the Traefik route configuration for the Hockeypuck service."""
        route_config = {
            "tcp": {
                "routers": {
                    "hockeypuck-tcp-router": {
                        "rule": "ClientIP(`0.0.0.0/0`)",
                        "service": "hockeypuck-tcp-service",
                        "entryPoints": ["reconciliation-port"],
                    }
                },
                "services": {
                    "hockeypuck-tcp-service": {
                        "loadBalancer": {"servers": [{"address": f"{socket.getfqdn()}:11370"}]}
                    }
                },
            }
        }
        return route_config
