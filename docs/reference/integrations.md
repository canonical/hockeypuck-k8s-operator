# Integrations

See [Integrations](https://charmhub.io/hockeypuck-k8s/integrations).

### `database`

_Interface_: `postgresql_client`
_Supported charms_: [Charmed PostgreSQL](https://charmhub.io/postgresql), [Charmed PostgreSQL-K8s](https://charmhub.io/postgresql-k8s)

The database endpoint can be integrated with PostgreSQL based charms, providing long term storage for Hockeypuck.
The database relation connects `hockeypuck-k8s` with charms that support the `postgresql_client` interface on port 5432
in the database side.

Example database integrate command: 
```
juju integrate hockeypuck-k8s postgresql-k8s
```

### `grafana-dashboard`

_Interface_: `grafana-dashboard`
_Supported charms_: [grafana-k8s](https://charmhub.io/grafana-k8s)

Grafana-dashboard is a part of the COS relation to enhance observability.
The relation enables quick dashboard access already tailored to fit the needs of
operators to monitor the charm. The template for the Grafana dashboard for the
Hockeypuck charm can be found at `/src/cos/grafana_dashboards/hockeypuck.json`.
In the Grafana UI, it can be found as “Hockeypuck metrics” under the General section of the 
dashboard browser (`/dashboards`). Modifications to the dashboard can be made but will not be 
persisted upon restart or redeployment of the charm.

The Hockeypuck charm satisfies the `grafana_dashboard` interface by providing the 
pre-made dashboard template to the Grafana relation data bag under the "dashboards" key. 
Requires Prometheus data source to be already integrated with Grafana.

Example Grafana-Prometheus integrate command: 
```
juju integrate grafana-k8s:grafana-source prometheus-k8s:grafana-source
```  
Example Grafana-dashboard integrate command: 
```
juju integrate hockeypuck-k8s grafana-dashboard
```

### `ingress`

_Interface_: `ingress`
_Supported charms_: [nginx-ingress-integrator](https://charmhub.io/nginx-ingress-integrator), [traefik-k8s](https://charmhub.io/traefik-k8s)

Ingress manages external HTTP/HTTPS access to services in a Kubernetes cluster.
Note that the Kubernetes cluster must already have an nginx ingress controller deployed. 
Documentation to enable ingress in MicroK8s can be found 
[here](https://microk8s.io/docs/addon-ingress).

Example ingress integrate command: 
```
juju integrate hockeypuck-k8s nginx-ingress-integrator
```

### `logging`

_Interface_: `loki_push_api`
_Supported charms_: [loki-k8s](https://charmhub.io/loki-k8s)

The logging relation is a part of the COS relation to enhance logging observability.
Logging relation through the `loki_push_api` interface installs and runs `promtail` which ships the
contents of the Hockeypuck kubernetes pod logs to Loki.
This can then be queried through the Loki API or easily visualized through Grafana. Learn more about COS
[here](https://charmhub.io/topics/canonical-observability-stack).

Example logging-endpoint integrate command: 
```
juju integrate hockeypuck-k8s loki-k8s
```

### `metrics-endpoint`

_Interface_: [`prometheus_scrape`](https://charmhub.io/interfaces/prometheus_scrape-v0)  
_Supported charms_: [prometheus-k8s](https://charmhub.io/prometheus-k8s)

The metrics-endpoint relation allows scraping the `/metrics` endpoint provided by Hockeypuck
on port 9626, which provides [Hockeypuck metrics](https://charmhub.io/hockeypuck-k8s/docs/reference-metrics). 

Example metrics-endpoint integrate command: 
```
juju integrate hockeypuck-k8s prometheus-k8s
```

### `traefik-route`

_Interface_: [`traefik_route`](https://charmhub.io/traefik-k8s/integrations#traefik-route)  
_Supported charms_: [traefik-k8s](https://charmhub.io/traefik-k8s)

The traefik-route relation provides low-level access to Traefik configuration. Hockeypuck requires 
this interface to expose the reconciliation port (11370) to [peer](https://hockeypuck.io/configuration.html#:~:text=1.4.-,Recon,-Hockeypuck%20supports%20the) with other key servers.

Example traefik-route integrate command: 
```
juju integrate hockeypuck-k8s traefik-k8s:traefik-route
```
