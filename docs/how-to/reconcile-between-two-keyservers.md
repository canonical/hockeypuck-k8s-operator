# Reconcile between two keyservers

Hockeypuck supports peering with other SKS-compatible keyservers to synchronize public key data through **reconciliation**.

1. Create a file `peers.txt` and add the external peers you want to reconcile with. Each line must be in the following format:
```
<peer_address>,<http_port>,<reconciliation_port>
```
* **peer_address**: The IP or fully qualified domain name (FQDN) of the peer.
* **http_port**: The port where the peer exposes its SKS HTTP API (usually 11371).
* **reconciliation_port**: The port used for reconciliation (usually 11370).

Example `peers.txt`:
```
10.1.39.11,11371,11370
10.1.39.13,11371,11370
```

2. Configure the Hockeypuck charm to use the file through the `external-peers` config option:
```bash
juju config hockeypuck-k8s external-peers=@peers.txt
```

3. Check the Hockeypuck logs to confirm that reconciliation with external peers is taking place:
```bash
kubectl logs hockeypuck-k8s-0 -c app -n $JUJU_MODEL_NAME
```
You might find logs that look like the one below. The following logs are extracted from a Hockeypuck keyserver deployed in a secondary model and reconciled with a keyserver deployed in a primary model with a single key:
```
2025-04-17T05:26:59.063Z [go] time="2025-04-17T05:26:59Z" level=info msg="accepted recon from [recon=10.1.39.177:11370, http=10.1.39.177:11371, weight=0, addr=<nil>, ips=[10.1.39.177]]" label="serve :11370"
2025-04-17T05:26:59.066Z [go] time="2025-04-17T05:26:59Z" level=info msg="reconciliation done" label="serve :11370" remoteAddr="10.1.39.177:42586"
2025-04-17T05:26:59.066Z [go] time="2025-04-17T05:26:59Z" level=info msg="recovering 1 items" label="serve :11370" remoteAddr="10.1.39.177:42586"
2025-04-17T05:26:59.106Z [go] time="2025-04-17T05:26:59Z" level=info POST=/pks/hashquery duration=6.395046ms host="10.1.39.140:11371" status-code=200
2025-04-17T05:26:59.115Z [go] time="2025-04-17T05:26:59Z" level=info msg="Bulk insertion skipped (small number of keys). Reverting to normal insertion."
2025-04-17T05:26:59.159Z [go] time="2025-04-17T05:26:59Z" level=info msg=upsert inserted=1 label="recon :11370" remoteAddr="10.1.39.177:42586" unchanged=0 updated=0
2025-04-17T05:26:59.160Z [go] time="2025-04-17T05:26:59Z" level=info msg="recovery complete" label="serve :11370" remoteAddr="10.1.39.177:42586"
```
