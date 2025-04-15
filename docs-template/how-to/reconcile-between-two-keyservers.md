# Reconcile between two keyservers

1. Create a file `peers.txt` and add the external peers to be configured in the following format:
```
peer_address,http_port1,reconciliation_port1
peer_address,http_port2,reconciliation_port2
```
The peer address can be either the peer's IP or FQDN.
For example:
```
10.1.39.11,11371,11370
10.1.39.13,11371,11370
```

2. Set the `external-peers` config option:
```bash
juju config hockeypuck-k8s external-peers=@peers.txt
```

3. Verify if reconciliation is happening successfully by checking the logs:
```bash
kubectl logs hockeypuck-k8s-0 -c app -n JUJU_MODEL_NAME
```
