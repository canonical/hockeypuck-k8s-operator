# How-to guides

The following guides cover key processes and common tasks for managing and using the Hockeypuck charm.

## Key management

Hockeypuck manages OpenPGP public keys, and the charm provides tools for both regular key operations and administrative key management. These guides explain how to manage keys through Juju actions and HTTP APIs, as well as how to configure admin keys for privileged operations like replacing or deleting keys.

- [Manage GPG keys](manage-gpg-keys.md)
- [Manage admin keys](manage-admin-keys.md)

## Integration and synchronisation

Hockeypuck can be integrated with the Canonical Observability Stack (COS) for monitoring and with other SKS-compatible key servers for synchronising public key data. These guides walk you through setting up those integrations.

- [Integrate with COS](integrate-with-cos.md)
- [Reconcile between two key servers](reconcile-between-two-keyservers.md)

## Update and maintenance

Over the lifecycle of your deployment, you may need to upgrade to a newer version of the charm or recover from a failure. These guides cover backing up and restoring Hockeypuck data via the PostgreSQL charm and upgrading to a new charm revision.

- [Back up and restore](backup-and-restore-hockeypuck.md)
- [Upgrade](upgrade.md)

## Development

- [Contribute](contribute.md)
