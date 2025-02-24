# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Traefik route observer module."""

import socket
import typing

import ops
from charms.traefik_k8s.v0.traefik_route import TraefikRouteRequirer

RELATION_NAME = "traefik-route"
HOCKEYPUCK_TCP_ROUTER = {
    "hockeypuck-tcp-router": {
        "rule": "ClientIP(`0.0.0.0/0`)",
        "service": "hockeypuck-tcp-service",
        "entryPoints": ["reconciliation-port"],
    }
}


class TraefikRouteObserver(ops.Object):
    """Traefik route relation observer."""

    def __init__(self, charm: ops.CharmBase):
        """Initialize the observer and register event handlers.

        Args:
            charm: The parent charm.
        """
        super().__init__(charm, RELATION_NAME)
        self._charm = charm
        self.traefik_route = TraefikRouteRequirer(
            self._charm, self.model.get_relation(RELATION_NAME), RELATION_NAME, raw=True
        )
        self._configure_traefik_route()

    def _configure_traefik_route(self) -> None:
        """Build the traefik-route configuration."""
        if self._charm.unit.is_leader() and self.traefik_route.is_ready():
            self.traefik_route.submit_to_traefik(self._route_config, static=self._static_config)

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
        address_list = []
        address_list.append({"address": f"{socket.getfqdn()}:11370"})
        secret_storage_relation = typing.cast(
            ops.Relation, self.model.get_relation("secret-storage")
        )
        unit_names = [unit.name for unit in secret_storage_relation.units]
        # unit fqdn format: <unit-name>.<app-name>-endpoints.<model-name>.svc.cluster.local
        for unit_name in unit_names:
            unit_name = unit_name.replace("/", "-")
            unit_fqdn = (
                f"{unit_name}."
                f"{self._charm.app.name}-endpoints."
                f"{self._charm.model.name}.svc"
            )
            address_list.append({"address": f"{unit_fqdn}:11370"})
        route_config = {
            "tcp": {
                "routers": HOCKEYPUCK_TCP_ROUTER,
                "services": {
                    "hockeypuck-tcp-service": {
                        "loadBalancer": {"servers": address_list},
                    }
                },
            }
        }
        return route_config
