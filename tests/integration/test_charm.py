#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

import logging
from typing import Dict, Optional

import ops
from charms.data_platform_libs.v0.data_interfaces import DatabaseCreatedEvent, DatabaseRequires

logger = logging.getLogger(__name__)


class HockeypuckCharm(ops.CharmBase):
    """Charmed Hockeypuck."""

    def __init__(self, framework: ops.Framework) -> None:
        super().__init__(framework)
        self.pebble_service_name = "hockeypuck-service"
        self.container = self.unit.get_container("hockeypuck")
        framework.observe(self.on.hockeypuck_pebble_ready, self._on_hockeypuck_pebble_ready)
        framework.observe(self.on.collect_unit_status, self._on_collect_status)
        # Charm events defined in the database requires charm library:
        self.database = DatabaseRequires(self, relation_name="database", database_name="hkp")
        framework.observe(self.database.on.database_created, self._on_database_created)
        framework.observe(self.database.on.endpoints_changed, self._on_database_created)

    def _on_collect_status(self, event: ops.CollectStatusEvent) -> None:
        if not self.model.get_relation("database"):
            # We need the user to do 'juju integrate'.
            event.add_status(ops.BlockedStatus("Waiting for database relation"))
        elif not self.database.fetch_relation_data():
            # We need the charms to finish integrating.
            event.add_status(ops.WaitingStatus("Waiting for database relation"))
        try:
            status = self.container.get_service(self.pebble_service_name)
        except (ops.pebble.APIError, ops.ModelError):
            event.add_status(ops.MaintenanceStatus("Waiting for Pebble in workload container"))
        else:
            if not status.is_running():
                event.add_status(ops.MaintenanceStatus("Waiting for the service to start up"))
        # If nothing is wrong, then the status is active.
        event.add_status(ops.ActiveStatus())

    def _on_hockeypuck_pebble_ready(self, event: ops.PebbleReadyEvent) -> None:
        self._update_layer_and_restart()

    def _on_database_created(self, event: DatabaseCreatedEvent) -> None:
        """Event is fired when postgres database is created."""
        self._update_layer_and_restart()

    def _update_layer_and_restart(self) -> None:
        """Define and start a workload using the Pebble API.

        You'll need to specify the right entrypoint and environment
        configuration for your specific workload. Tip: you can see the
        standard entrypoint of an existing container using docker inspect

        Learn more about interacting with Pebble at https://juju.is/docs/sdk/pebble
        Learn more about Pebble layers at
            https://canonical-pebble.readthedocs-hosted.com/en/latest/reference/layers
        """

        # Learn more about statuses in the SDK docs:
        # https://juju.is/docs/sdk/constructs#heading--statuses
        self.unit.status = ops.MaintenanceStatus("Assembling Pebble layers")
        try:
            # Get the current pebble layer config
            services = self.container.get_plan().to_dict().get("services", {})
            if services != self._pebble_layer.to_dict().get("services", {}):
                # Changes were made, add the new layer
                self.container.add_layer("hockeypuck", self._pebble_layer, combine=True)
                logger.info("Added updated layer 'hockeypuck' to Pebble plan")

                self.container.restart(self.pebble_service_name)
                logger.info(f"Restarted '{self.pebble_service_name}' service")
        except ops.pebble.APIError as e:
            logger.info("Unable to connect to Pebble: %s", e)
            return

    @property
    def app_environment(self) -> Dict[str, Optional[str]]:
        """This property method creates a dictionary containing environment variables
        for the application. It retrieves the database authentication data by calling
        the `fetch_postgres_relation_data` method and uses it to populate the dictionary.
        If any of the values are not present, it will be set to None.
        The method returns this dictionary as output.
        """
        db_data = self.fetch_postgres_relation_data()
        if not db_data:
            return {}
        env = {
            "POSTGRES_HOST": db_data.get("db_host", None),
            "POSTGRES_PORT": db_data.get("db_port", None),
            "POSTGRES_USER": db_data.get("db_username", None),
            "POSTGRES_PASSWORD": db_data.get("db_password", None),
        }
        return env

    def fetch_postgres_relation_data(self) -> Dict[str, str]:
        """Fetch postgres relation data.

        This function retrieves relation data from a postgres database using
        the `fetch_relation_data` method of the `database` object. The retrieved data is
        then logged for debugging purposes, and any non-empty data is processed to extract
        endpoint information, username, and password. This processed data is then returned as
        a dictionary. If no data is retrieved, the unit is set to waiting status and
        the program exits with a zero status code."""
        relations = self.database.fetch_relation_data()
        logger.debug("Got following database data: %s", relations)
        for data in relations.values():
            if not data:
                continue
            host, port = data["endpoints"].split(":")
            db_data = {
                "db_host": host,
                "db_port": port,
                "db_username": data["username"],
                "db_password": data["password"],
            }
            return db_data
        return {}

    @property
    def _pebble_layer(self) -> ops.pebble.Layer:
        """A Pebble layer for the FastAPI demo services."""
        command = "hockeypuck/bin/hockeypuck -config /hockeypuck/etc/hockeypuck.conf"
        pebble_layer: ops.pebble.LayerDict = {
            "summary": "FastAPI demo service",
            "description": "pebble config layer for FastAPI demo server",
            "services": {
                self.pebble_service_name: {
                    "override": "replace",
                    "summary": "fastapi demo",
                    "command": command,
                    "startup": "enabled",
                    "environment": self.app_environment,
                }
            },
        }
        return ops.pebble.Layer(pebble_layer)


if __name__ == "__main__":
    ops.main(HockeypuckCharm)
