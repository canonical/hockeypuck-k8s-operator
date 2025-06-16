# Hockeypuck ports

Hockeypuck exposes the following ports for its operation:

1. **Web App port** (11371): This port serves the Hockeypuck web UI as well as its SKS-compatible APIs. It is made externally accessible when the charm is integrated with an ingress controller like traefik-k8s.
2. **Reconciliation port** (11370): This port is used for peering with other SKS-compatible key servers to synchronize key data. It is accessible via the traefik-route relation.
3. **Metrics port** (9626): Hockeypuck exports Prometheus-compatible metrics at this port via the `/metrics` endpoint.
