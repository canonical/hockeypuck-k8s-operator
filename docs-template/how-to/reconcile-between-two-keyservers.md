# Reconcile between two keyservers

Hockeypuck supports peering with other SKS-compatible keyservers to synchronize public key data through **reconciliation**.

## Steps to configure reconciliation

1. Create a file `peers.txt` and add the external peers you want to reconcile with. Each line must be in the following format:
```
<peer_address>,<http_port>,<reconciliation_port>
```
* **peer_address**: The IP or fully qualified domain name (FQDN) of the peer
* **http_port**: The port where the peer exposes its SKS HTTP API (usually 11371)
* **reconciliation_port**: The port used for reconciliation (usually 11370)

Example `peers.txt`:
```
10.1.39.11,11371,11370
10.1.39.13,11371,11370
```

2. Configure the `hockeypuck-k8s` charm to use the file through the `external-peers` config option:
```bash
juju config hockeypuck-k8s external-peers=@peers.txt
```

3. Check the Hockeypuck logs to confirm that reconciliation with external peers is taking place:
```bash
kubectl logs hockeypuck-k8s-0 -c app -n $JUJU_MODEL_NAME
```
