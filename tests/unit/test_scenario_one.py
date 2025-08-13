from ops import testing

from src.charm import HockeypuckK8SCharm

METADATA = {
    "name": "hockeypuck-k8s",
    "title": "Hockeypuck K8S Charm",
    "summary": "Hockeypuck OpenPGP public keyserver",
    "description": "reduced for simplicity",
    "base": "ubuntu@24.04",
    "build-base": "ubuntu@24.04",
    "platforms": {"amd64": {"build-on": ["amd64"], "build-for": ["amd64"]}},
    "parts": {
        "charm": {
            "plugin": "charm",
            "source": ".",
            "build-snaps": ["rustup"],
            "override-build": "rustup default stable\ncraftctl default",
        }
    },
    "type": "charm",
    "charm-libs": [
        {"lib": "traefik-k8s.ingress", "version": "2"},
        {"lib": "observability-libs.juju_topology", "version": "0"},
        {"lib": "grafana-k8s.grafana_dashboard", "version": "0"},
        {"lib": "loki-k8s.loki_push_api", "version": "1"},
        {"lib": "data-platform-libs.data_interfaces", "version": "0"},
        {"lib": "prometheus-k8s.prometheus_scrape", "version": "0"},
        {"lib": "redis-k8s.redis", "version": "0"},
        {"lib": "data-platform-libs.s3", "version": "0"},
        {"lib": "saml-integrator.saml", "version": "0"},
        {"lib": "tempo-coordinator-k8s.tracing", "version": "0"},
        {"lib": "smtp-integrator.smtp", "version": "0"},
        {"lib": "openfga-k8s.openfga", "version": "1"},
    ],
    "actions": {
        "block-keys": {
            "description": "Blocklist and delete keys from the keyserver database.",
            "properties": {
                "fingerprints": {
                    "type": "string",
                    "description": "Comma-separated list of full fingerprints to ignore (minus the leading 0x).",
                },
                "comment": {
                    "type": "string",
                    "description": "Any comment to pass along with the action.",
                },
            },
            "required": ["fingerprints", "comment"],
        },
        "rebuild-prefix-tree": {
            "description": "The prefix tree is used to manage the reconciliation process and \nmust always be in sync with the database. If you suspect it is corrupted or out \nof sync, or if the prefix tree needs to be removed and rebuilt after pg_restore, \nit can be done with this action. \n"
        },
        "lookup-key": {
            "description": "Look up a key by fingerprint / email-id / keyword.",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "Keyword to search for in the keyserver database. Note that the entire fingerprint \nincluding the preceding '0x' is required for fingerprint search.\n",
                }
            },
            "required": ["keyword"],
        },
        "rotate-secret-key": {
            "description": "Rotate the secret key. Users will be forced to log in again. This might be useful if a security breach occurs."
        },
    },
    "assumes": ["k8s-api"],
    "containers": {"app": {"resource": "app-image"}},
    "peers": {"secret-storage": {"interface": "secret-storage"}},
    "provides": {
        "metrics-endpoint": {"interface": "prometheus_scrape"},
        "grafana-dashboard": {"interface": "grafana_dashboard"},
    },
    "requires": {
        "postgresql": {"interface": "postgresql_client", "optional": False, "limit": 1},
        "traefik-route": {"interface": "traefik_route", "limit": 1, "optional": True},
        "logging": {"interface": "loki_push_api"},
        "ingress": {"interface": "ingress", "limit": 1},
    },
    "resources": {"app-image": {"type": "oci-image", "description": "go application image."}},
    "links": {
        "contact": "https://launchpad.net/~canonical-is-devops",
        "documentation": "https://discourse.charmhub.io/t/hockeypuck-documentation-overview/16591",
        "issues": "https://github.com/canonical/hockeypuck-k8s-operator/issues",
        "source": "https://github.com/canonical/hockeypuck-k8s-operator",
    },
    "config": {
        "options": {
            "external-peers": {
                "type": "string",
                "description": "New line separated list of external peer IPs or FQDNs that are provided in the \nfollowing format:\npeer_address,http_port1,reconciliation_port1\npeer_address,http_port2,reconciliation_port2\n",
            },
            "contact-fingerprint": {
                "type": "string",
                "description": "Full fingerprint of the keyserver administrator. It is strongly recommended \nthat the server contact advertised on the stats page is not one of the admin keys.\n",
            },
            "admin-keys": {
                "type": "string",
                "description": "A comma-separated list of fingerprints that identify keys that may\nsign administration requests for this server.\n",
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
                "description": "Long secret you can use for sessions, csrf or any other thing where you need a random secret shared by all units",
            },
            "app-secret-key-id": {
                "type": "secret",
                "description": 'This configuration is similar to `app-secret-key`, but instead accepts a Juju user secret ID. The secret should contain a single key, "value", which maps to the actual application secret key. To create the secret, run the following command: `juju add-secret my-app-secret-key value=<secret-string> && juju grant-secret my-app-secret-key my-app`, and use the output secret ID to configure this option.',
            },
        }
    },
}


def test_base_one():
    """
    Integrate postgresql with hockeypuck and scale to 2 units and check if the
    charm is blocked. Provide the metadata as is in json format.
    """
    ctx = testing.Context(HockeypuckK8SCharm, meta=METADATA)
    relation1 = testing.Relation("postgresql")
    state_in = testing.State(planned_units=2, relations=[relation1])
    state_out = ctx.run(ctx.on.start(), state_in)
    assert state_out.unit_status == testing.BlockedStatus(
        "Hockeypuck does not support multi-unit deployments"
    )
