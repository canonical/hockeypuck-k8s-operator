# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Traefik route observer module."""

import socket
import typing

import ops
from charms.traefik_k8s.v0.traefik_route import TraefikRouteRequirer
from paas_charm.relations import CustomRelation, OnChange

from actions import RECONCILIATION_PORT

RELATION_NAME = "traefik-route"
PEERS_RELATION_NAME = "peers"
HOCKEYPUCK_TCP_ROUTER = {
    "hockeypuck-tcp-router": {
        "rule": "ClientIP(`0.0.0.0/0`)",
        "service": "hockeypuck-tcp-service",
        "entryPoints": ["reconciliation-port"],
    }
}


class TraefikRouteRelation(CustomRelation):
    """Traefik route custom relation.

    The relation only publishes the reconciliation TCP route to Traefik, it neither
    contributes to the workload environment nor blocks the workload.

    Attrs:
        relation_name: Name of the traefik-route endpoint.
    """

    relation_name = RELATION_NAME

    def setup(self, on_change: OnChange) -> None:
        """Wire the relation events and create the requirer.

        Args:
            on_change: Reconcile callback injected by the framework, unused because the
                relation has no impact on the workload.
        """
        del on_change
        self._requirer = TraefikRouteRequirer(
            self.charm, self.model.get_relation(RELATION_NAME), RELATION_NAME, raw=True
        )
        on = self.charm.on
        for event in (
            self._requirer.on.ready,
            on[RELATION_NAME].relation_joined,
            on[PEERS_RELATION_NAME].relation_joined,
            on[PEERS_RELATION_NAME].relation_departed,
            on.leader_elected,
            on.upgrade_charm,
            on.config_changed,
        ):
            self.charm.framework.observe(event, self._configure_traefik_route)

    def _configure_traefik_route(self, _: typing.Optional[ops.EventBase] = None) -> None:
        """Build the traefik-route configuration."""
        if self.charm.unit.is_leader() and self._requirer.is_ready():
            self._requirer.submit_to_traefik(self._route_config, static=self._static_config)

    @property
    def _static_config(self) -> dict[str, dict[str, dict[str, str]]]:
        """Return the static configuration for the Hockeypuck service.

        Returns:
            The static configuration for traefik.
        """
        entry_points = {"reconciliation-port": {"address": f":{RECONCILIATION_PORT}"}}
        return {
            "entryPoints": entry_points,
        }

    @property
    def _route_config(self) -> dict[str, dict[str, object]]:
        """Return the Traefik route configuration for the Hockeypuck service."""
        address_list = []
        address_list.append({"address": f"{socket.getfqdn()}:{RECONCILIATION_PORT}"})
        peers_relation = self.model.get_relation(PEERS_RELATION_NAME)
        unit_names = [unit.name for unit in peers_relation.units] if peers_relation else []
        # unit fqdn format: <unit-name>.<app-name>-endpoints.<model-name>.svc.cluster.local
        for unit_name in unit_names:
            unit_name = unit_name.replace("/", "-")
            app_name, model_name = self.charm.app.name, self.charm.model.name
            unit_fqdn = f"{unit_name}.{app_name}-endpoints.{model_name}.svc"
            address_list.append({"address": f"{unit_fqdn}:{RECONCILIATION_PORT}"})
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
