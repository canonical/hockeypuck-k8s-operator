# Back up and restore
A backup is a snapshot of the Hockeypuck data (public keys, subkeys, blocked keys) at a given point in time. This backup can be used to:
* Restore Hockeypuck to a previous stable state (during disaster recovery).
* Migrate data to a new Hockeypuck charm instance.

# Requirements
* Access to an AWS S3 storage with its secret key and access key.

## Create a backup

1. Remove the relation between the Hockeypuck charm and the PostgreSQL charm:
```bash
juju remove-relation postgresql-k8s:database hockeypuck-k8s:postgresql
```
2. Since the Hockeypuck data is stored in the PostgreSQL database, the PostgreSQL data needs to be backed up. Instructions to back up the PostgreSQL data can be found in the PostgreSQL charm [backup documentation](https://charmhub.io/postgresql-k8s/docs/h-configure-s3-aws).


## Restore the backup on a new charm instance

[note]
If you are trying to restore a backup that was made from a different cluster, check out the [PostgreSQL Charmhub documentation](https://charmhub.io/postgresql-k8s/docs/h-migrate-cluster).
[/note]


1. Restore the backup on the PostgreSQL charm unit by following the instructions in the PostgreSQL charm [restoration documentation](https://charmhub.io/postgresql-k8s/docs/h-restore-backup).

2. Integrate the Hockeypuck charm with the PostgreSQL charm:
```shell
juju integrate hockeypuck-k8s postgresql-k8s
```

3. Run the `rebuild-prefix-tree` action:
```shell
juju run hockeypuck-k8s/0 rebuild-prefix-tree
```
This could take a couple of hours to complete depending on the number of keys in the database.
