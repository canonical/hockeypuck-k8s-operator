---
myst:
  html_meta:
    "description lang=en": "How-to guides for Hockeypuck charm, including basic operations, upgrades, and development."
---

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

## Maintenance and development

Over the lifecycle of your deployment, you may need to upgrade to a newer version of the charm, recover from a failure, or even contribute new features or bug fixes. These guides cover backing up and restoring Hockeypuck data via the PostgreSQL charm, upgrading to a new charm revision, and contributing to the project.

- [Back up and restore](backup-and-restore-hockeypuck.md)
- [Upgrade](upgrade.md)
- [Contribute](contribute.md)
