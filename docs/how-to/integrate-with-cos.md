# Integrate with COS

## Deploy COS Lite
Create a Juju model and deploy the Canonical Observability Stack bundle [cos-lite](https://charmhub.io/topics/canonical-observability-stack) to this model:

```bash
juju add-model cos-lite
juju deploy cos-lite --trust
```

## Expose the application relation endpoints
Once all the COS Lite applications are deployed and settled down (you can monitor this by using `juju status --watch 2s`), expose the relation points for Prometheus, Loki and Grafana:

```bash
juju offer prometheus:metrics-endpoint
juju offer loki:logging
juju offer grafana:grafana-dashboard
```

Validate that the offers have been successfully created by running:

```bash
juju find-offers cos-lite
```

You should see something similar to the output below:

```bash
Store                 URL                        Access  Interfaces
tutorial-controller  admin/cos-lite.loki        admin   loki_push_api:logging
tutorial-controller  admin/cos-lite.prometheus  admin   prometheus_scrape:metrics-endpoint
tutorial-controller  admin/cos-lite.grafana     admin   grafana_dashboard:grafana-dashboard
```

## Integrate Hockeypuck

Switch back to the charm model and integrate your charm with the exposed endpoints:

```bash
juju switch <Hockeypuck charm model>
juju integrate hockeypuck-k8s admin/cos-lite.grafana
juju integrate hockeypuck-k8s admin/cos-lite.loki
juju integrate hockeypuck-k8s admin/cos-lite.prometheus
```

This effectively integrates your application with Prometheus, Loki, and Grafana.
