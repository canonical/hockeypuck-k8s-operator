# Hockeypuck Kubernetes operator

The Hockeypuck Kubernetes operator is a [Juju charm](https://canonical.com/juju/docs/juju-cli/3.6/reference/charm/) that deploys and manages [Hockeypuck](https://hockeypuck.io/), an OpenPGP public keyserver, on Kubernetes.

DevOps and SRE teams can use the charm to run a service for publishing and looking up public keys.

## In this documentation

| | |
| --- | --- |
| **Get started** | [Deploy your first Hockeypuck keyserver](https://charmhub.io/hockeypuck-k8s/docs/tutorial-getting-started) |
| **Deployment and architecture** | [Charm architecture](https://charmhub.io/hockeypuck-k8s/docs/explanation-charm-architecture) \| [Configuration options](https://charmhub.io/hockeypuck-k8s/docs/reference-configurations) \| [Juju relation endpoints](https://charmhub.io/hockeypuck-k8s/docs/reference-integrations) \| [Network ports](https://charmhub.io/hockeypuck-k8s/docs/reference-ports) |
| **Key management** | [Manage OpenPGP keys](https://charmhub.io/hockeypuck-k8s/docs/how-to-manage-gpg-keys) \| [Manage admin keys](https://charmhub.io/hockeypuck-k8s/docs/how-to-manage-admin-keys) \| [Juju actions](https://charmhub.io/hockeypuck-k8s/docs/reference-actions) |
| **Keyserver peering** | [Synchronise keys between servers](https://charmhub.io/hockeypuck-k8s/docs/how-to-reconcile-between-two-keyservers) |
| **Maintenance and recovery** | [Upgrade the charm](https://charmhub.io/hockeypuck-k8s/docs/how-to-upgrade) \| [Back up and restore keyserver data](https://charmhub.io/hockeypuck-k8s/docs/how-to-backup-and-restore-hockeypuck) |
| **Observability** | [Integrate with Canonical Observability Stack](https://charmhub.io/hockeypuck-k8s/docs/how-to-integrate-with-cos) \| [Server and reconciliation metrics](https://charmhub.io/hockeypuck-k8s/docs/reference-metrics) |
| **Security** | [Risks and best practices](https://charmhub.io/hockeypuck-k8s/docs/explanation-security) |

## How this documentation is organised

This documentation uses the [Diátaxis documentation structure](https://diataxis.fr/).

- The [tutorial](https://charmhub.io/hockeypuck-k8s/docs/tutorial-getting-started) walks you through deploying Hockeypuck on Kubernetes and accessing its web interface.
- The [how-to guides on GitHub](https://github.com/canonical/hockeypuck-k8s-operator/blob/main/docs/how-to/index.md) show you how to manage keys, set up peering and monitoring, and maintain a running keyserver.
- The [reference on GitHub](https://github.com/canonical/hockeypuck-k8s-operator/blob/main/docs/reference/index.md) describes the charm's actions, configuration options, relation endpoints, network ports, and metrics.
- The [security explanation](https://charmhub.io/hockeypuck-k8s/docs/explanation-security) covers risks such as data loss and unencrypted traffic, and how to reduce them.

## Project and community

The Hockeypuck Kubernetes operator is an open-source project in the Ubuntu family. We welcome contributions to the charm and its documentation.

- Get support on the [Discourse forum](https://discourse.charmhub.io/) or join the [Matrix chat](https://matrix.to/#/#charmhub-charmdev:ubuntu.com).
- Contribute to the [charm](https://github.com/canonical/hockeypuck-k8s-operator/blob/main/CONTRIBUTING.md) or [documentation](https://charmhub.io/hockeypuck-k8s/docs/how-to-contribute).
- Report bugs or suggest improvements on [GitHub Issues](https://github.com/canonical/hockeypuck-k8s-operator/issues).
- Track changes across charm revisions in the [changelog](https://charmhub.io/hockeypuck-k8s/docs/changelog).
- Read the [Ubuntu Code of Conduct](https://ubuntu.com/community/code-of-conduct).

# Contents

1. [Changelog](changelog.md)
1. [Explanation](explanation)
  1. [Security](explanation/security.md)
1. [How To](how-to/index.md)
  1. [Back up and restore](how-to/backup-and-restore-hockeypuck.md)
  1. [How to contribute](how-to/contribute.md)
  1. [Integrate with COS](how-to/integrate-with-cos.md)
  1. [Manage admin keys in Hockeypuck](how-to/manage-admin-keys.md)
  1. [Manage GPG keys](how-to/manage-gpg-keys.md)
  1. [Reconcile between two key servers](how-to/reconcile-between-two-keyservers.md)
  1. [Upgrade](how-to/upgrade.md)
1. [Reference](reference/index.md)
  1. [Actions](reference/actions.md)
  1. [Charm architecture](reference/charm-architecture.md)
  1. [Configurations](reference/configurations.md)
  1. [Integrations](reference/integrations.md)
  1. [Metrics](reference/metrics.md)
  1. [Hockeypuck ports](reference/ports.md)
1. [Tutorial](tutorial)
  1. [Deploy the Hockeypuck charm for the first time](tutorial/getting-started.md)
