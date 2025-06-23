# Metrics

The following metrics are provided by the workload container at the `/metrics` endpoint at port 9626.

## Server metrics

* **hockeypuck_keys_added**: Number of new keys added since startup.
* **hockeypuck_keys_added_jitter**: Number of lost PTree (Probabilistic Tree) entries recreated.
* **hockeypuck_keys_ignored**: Number of keys with no-op (unchanged) updates.
* **hockeypuck_keys_removed**: Number of keys removed since startup.
* **hockeypuck_keys_removed_jitter**: Number of stale PTree entries cleaned up.
* **hockeypuck_keys_updated**: Number of keys that have been updated.
* **hockeypuck_http_request_duration_seconds**: Time spent generating HTTP responses.

## Reconciliation metrics

* **conflux_reconciliation_items_recovered**: Count of items recovered since startup.
* **conflux_reconciliation_busy_peer**: Count of reconciliations attempted against busy peers since startup.
* **conflux_reconciliation_duration_seconds**: Time spent performing a reconciliation, in seconds.
* **conflux_reconciliation_event_time_seconds**: When the given event last occurred, in seconds since the epoch.
* **conflux_reconciliation_failure**: Count of failed reconciliations since startup.
* **conflux_reconciliation_success**: Count of successful reconciliations since startup.

Apart from these, there are [Go runtime metrics](https://pkg.go.dev/runtime/metrics) and process-level metrics also available.