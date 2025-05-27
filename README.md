# hockeypuck-k8s-operator

[![CharmHub Badge](https://charmhub.io/hockeypuck-k8s/badge.svg)](https://charmhub.io/hockeypuck-k8s)
[![Publish to edge](https://github.com/canonical/hockeypuck-k8s-operator/actions/workflows/publish_charm.yaml/badge.svg)](https://github.com/canonical/hockeypuck-k8s-operator/actions/workflows/publish_charm.yaml)
[![Promote charm](https://github.com/canonical/hockeypuck-k8s-operator/actions/workflows/promote_charm.yaml/badge.svg)](https://github.com/canonical/hockeypuck-k8s-operator/actions/workflows/promote_charm.yaml)
[![Discourse Status](https://img.shields.io/discourse/status?server=https%3A%2F%2Fdiscourse.charmhub.io&style=flat&label=CharmHub%20Discourse)](https://discourse.charmhub.io)

A [Juju](https://juju.is/) [12-factor](https://documentation.ubuntu.com/juju/3.6/reference/charm/#factor-app-charm) [charm](https://documentation.ubuntu.com/juju/3.6/reference/charm/) deploying and managing [Hockeypuck](https://hockeypuck.io/) on Kubernetes. Hockeypuck is an [OpenPGP](https://www.openpgp.org/) public keyserver tool used to manage public key infrastructure for PGP (Pretty Good Privacy). PGP is a system for securing communication through encryption and digital signatures.

The server provides interfaces to add, look up, replace and delete public keys from the keyserver. Hockeypuck can synchronize public key material with SKS (Synchronizing Key Server) and other Hockeypuck servers. It implements the HTTP Keyserver Protocol and the SKS database reconciliation protocol.

For DevOps and SRE teams, this charm will make operating Hockeypuck simple and straightforward through Juju's clean interface.

For information about how to deploy, integrate, and manage this charm, see the official [hockeypuck-k8s charm documentation](https://charmhub.io/hockeypuck-k8s).

## Get started

To begin, refer to the [tutorial](https://charmhub.io/hockeypuck-k8s/docs/tutorial-getting-started) for step-by-step instructions.

### Basic operations

The following actions are available for this charm:

* **block-keys**: Blocklist and delete keys from the keyserver database.
* **rebuild-prefix-tree**: Rebuild the prefix tree used by Hockeypuck.
* **lookup-key**: Look up a key by fingerprint / email-id / keyword.

You can obtain more information on the actions [here](https://charmhub.io/hockeypuck-k8s/actions).

## Learn more

- [Read more](https://charmhub.io/hockeypuck-k8s/docs)
- [Official Webpage](https://hockeypuck.io/)
- [Troubleshooting](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)

## Project and community

The hockeypuck-k8s-operator is a member of the Ubuntu family. It's an open source project that warmly welcomes community projects, contributions, suggestions, fixes and constructive feedback.

* [Issues](https://github.com/canonical/hockeypuck-k8s-operator/issues)
* [Contributing](https://github.com/canonical/hockeypuck-k8s-operator/blob/main/CONTRIBUTING.md)
* [Matrix](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)
