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

Ensure that Hockeypuck and the COS Lite applications are settled down (you can monitor this by using `juju status --watch 2s`).

Obtain the Grafana dashboard credentials by running the `get-admin-password` action:

```bash
juju switch cos-lite
juju run grafana/0 get-admin-password
```

This action returns the URL and the admin password to access the Hockeypuck dashboard. Now, on your host machine, open a web browser, enter the Grafana URL, and use the username “admin” and your Grafana password to log in. Under **Home > Dashboards**, you should be able to see the Hockeypuck dashboard listed.

This effectively integrates your application with Prometheus, Loki, and Grafana.
