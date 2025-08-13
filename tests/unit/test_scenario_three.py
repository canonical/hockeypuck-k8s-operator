from ops import CharmBase, testing

from src.charm import HockeypuckK8SCharm

METADATA = {
    "name": "hockeypuck-k8s",
    "requires": {
        "postgresql": {
            "interface": "postgresql",
            "optional": False,
        },
        "traefik-route": {
            "interface": "traefik_route",
        },
        "ingress": {
            "interface": "ingress",
            "limit": 1,
        },
        "logging": {
            "interface": "loki_push_api",
        },
    },
    "peers": {
        "secret-storage": {
            "interface": "secret-storage",
        },
    },
    "containers": {
        "app": {
            "resource": "app-image",
        },
    },
    "resources": {
        "app-image": {
            "type": "oci-image",
            "description": "The OCI image to deploy.",
        },
    },
    "provides": {
        "metrics-endpoint": {
            "interface": "prometheus_scrape",
        },
        "grafana-dashboard": {
            "interface": "grafana_dashboard",
        },
    },
    "config": {
        "options": {
            "external-peers": {
                "type": "string",
                "description": (
                    "New line separated list of external peer IPs or FQDNs that are "
                    "provided in the \nfollowing format:\n"
                    "peer_address,http_port1,reconciliation_port1\n"
                    "peer_address,http_port2,reconciliation_port2\n"
                ),
            },
            "contact-fingerprint": {
                "type": "string",
                "description": (
                    "Full fingerprint of the keyserver administrator. It is strongly "
                    "recommended \nthat the server contact advertised on the stats page "
                    "is not one of the admin keys.\n"
                ),
            },
            "admin-keys": {
                "type": "string",
                "description": (
                    "A comma-separated list of fingerprints that identify keys that may\n"
                    "sign administration requests for this server."
                ),
            },
            "app-port": {
                "type": "int",
                "default": 8080,
                "description": "Default port where the application will listen on.",
            },
            "metrics-port": {
                "type": "int",
                "default": 8080,
                "description": "Port where the prometheus metrics will be scraped.",
            },
            "metrics-path": {
                "type": "string",
                "default": "/metrics",
                "description": "Path where the prometheus metrics will be scraped.",
            },
            "app-secret-key": {
                "type": "string",
                "description": (
                    "Long secret you can use for sessions, csrf or any other thing where "
                    "you need a random secret shared by all units"
                ),
            },
            "app-secret-key-id": {
                "type": "secret",
                "description": (
                    "This configuration is similar to `app-secret-key`, but instead "
                    "accepts a Juju user secret ID. The secret should contain a single key, "
                    '"value", which maps to the actual application secret key. To create '
                    "the secret, run the following command: `juju add-secret my-app-secret-key "
                    "value=<secret-string> && juju grant-secret my-app-secret-key go-app`, and "
                    "use the output secret ID to configure this option."
                ),
            },
        }
    },
}
ACTIONS = {
    "rotate-secret-key": {
        "description": "Rotate the secret key.",
    }
}

CONFIG = {
    "options": {
        "external-peers": {
            "type": "string",
            "description": (
                "New line separated list of external peer IPs or FQDNs that are "
                "provided in the \nfollowing format:\n"
                "peer_address,http_port1,reconciliation_port1\n"
                "peer_address,http_port2,reconciliation_port2\n"
            ),
        },
        "contact-fingerprint": {
            "type": "string",
            "description": (
                "Full fingerprint of the keyserver administrator. It is strongly "
                "recommended \nthat the server contact advertised on the stats page "
                "is not one of the admin keys.\n"
            ),
        },
        "admin-keys": {
            "type": "string",
            "description": (
                "A comma-separated list of fingerprints that identify keys that may\n"
                "sign administration requests for this server."
            ),
        },
    },
}


def test_base_three():
    """
    Integrate postgresql with hockeypuck and scale to 2 units and check if the
    charm is blocked. Provide the metadata, actions and config as json. Also repeat config in
    metadata section since there are key errors.
    """
    ctx = testing.Context(HockeypuckK8SCharm, meta=METADATA, actions=ACTIONS, config=CONFIG)
    relation1 = testing.Relation("postgresql")
    # relation3 = testing.Relation("ingress")
    # relation2 = testing.PeerRelation("secret-storage")x
    state_in = testing.State(planned_units=2, relations=[relation1])
    state_out = ctx.run(ctx.on.start(), state_in)
    assert state_out.unit_status == testing.BlockedStatus(
        "Hockeypuck does not support multi-unit deployments"
    )
