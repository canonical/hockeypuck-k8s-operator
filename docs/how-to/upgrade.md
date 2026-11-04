# Upgrade

Before updating the charm you need to back up the database using the PostgreSQL charm’s create-backup action.

```bash
juju run postgresql-k8s/leader create-backup
```

Additional information can be found about backing up in the [PostgreSQL charm's documentation](https://charmhub.io/postgresql-k8s/docs/h-configure-s3-aws).

If you deployed with the `app-port` or `metrics-port` options, unset them first, because the charm no longer has these options:

```bash
juju config hockeypuck-k8s --reset app-port,metrics-port
```

Then you can upgrade the Hockeypuck charm:

```bash
juju refresh hockeypuck-k8s --base ubuntu@26.04
```
After upgrading the Hockeypuck charm you need to rebuild the prefix tree:

```bash
juju run hockeypuck-k8s/0 rebuild-prefix-tree
```