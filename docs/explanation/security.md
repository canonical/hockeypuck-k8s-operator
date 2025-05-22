# Security

This document outlines common risks and possible best practices for the Hockeypuck charm. It focuses on configurations and protections available through the charm itself.

For details regarding upstream Hockeypuck configuration and broader security considerations, please refer to the [official Hockeypuck documentation](https://hockeypuck.io/configuration.html).

## Risks

The following items include descriptions of the risks, their corresponding best practices for mitigation, as well as links to related documentation and configuration guidelines.

### Loss of data

The Hockeypuck database might become inaccessible, corrupted, or may be destroyed.

#### Best practices

- Set up regular backups:

  Follow the [charm documentation](https://charmhub.io/hockeypuck-k8s/docs/how-to-backup-and-restore-hockeypuck) for guidance on creating regular backups and restoring them when required.
  
  The Hockeypuck charm maintains a table `deleted_keys` that contains a list of all the blocklisted keys. This table is read and fed into the `hockypuck.conf` file used by Hockeypuck during the startup process. If this data is lost, Hockeypuck will not block any keys during startup. It is important to have a backup of the charm to avoid the blocked keys from being reconciled while peering.

- Avoid manual key deletion:

  Manually deleting PGP keys from the PostgreSQL database does not remove the key entirely from Hockeypuck. Hockeypuck maintains another leveldb database locally apart from the PostgreSQL database to build the prefix tree. Deleting the key from PostgreSQL does not delete the key from the leveldb database. To ensure the key is properly removed from Hockeypuck, refer to [How to manage GPG keys](https://charmhub.io/hockeypuck-k8s/docs/how-to-manage-gpg-keys) on how to use Hockeypuck's `delete` API or the `block-keys` action.

### Denial-of-Service (DoS) attacks

A denial-of-service attack could overwhelm Hockeypuck with traffic, preventing legitimate users from accessing the service. Following the recent [DoS attack on keyservers](https://gist.github.com/rjhansen/67ab921ffb4084c865b3618d6955275f), implementing the [DoS protection rules](https://github.com/hockeypuck/hockeypuck/tree/master/contrib/docker-compose/standalone/haproxy/etc) provided by Hockeypuck is mandatory to allow peering with other external servers.

[note]
The current Hockeypuck charm does not have the DoS protection rules implemented due to implementation constraints and hence will not be able to reconcile with external peers. The DoS protection will be incorporated in future releases.
[/note]

### Security vulnerabilities

Running Hockeypuck with one or more weaknesses can be exploited by attackers.

#### Best practices

- Keep the Juju and the charm updated. See more about Juju updates in the [documentation](https://documentation.ubuntu.com/juju/latest/explanation/juju-security/index.html#regular-updates-and-patches).

### Unencrypted traffic

When HTTPS is not enabled, personal data exchanged between Hockeypuck and its users is transmitted in plain text. This leaves the interactions vulnerable to interception, tampering, and impersonation by malicious actors.

#### Best practices

- Always enable HTTPS:
  
  Configure Hockeypuck to use HTTPS for all interactions. The Hockeypuck charm supports ingress integration, allowing HTTPS to be enabled when integrating with charms such as [nginx-ingress-integrator](https://charmhub.io/nginx-ingress-integrator) and [traefik-k8s](https://charmhub.io/traefik-k8s).