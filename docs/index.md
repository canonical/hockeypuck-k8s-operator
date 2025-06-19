# Hockeypuck Kubernetes operator

A [Juju](https://juju.is/) [charm](https://documentation.ubuntu.com/juju/3.6/reference/charm/) deploying and managing [Hockeypuck](https://hockeypuck.io/) on Kubernetes. Hockeypuck is an OpenPGP public key server tool used to manage public key infrastructure for PGP (Pretty Good Privacy). PGP is a system for securing communication through encryption and digital signatures.

The server provides interfaces to add, look up, replace and delete public keys from the key server. Hockeypuck can synchronize public key material with SKS (Synchronizing Key Server) and other Hockeypuck servers. It implements the HTTP Keyserver Protocol and the SKS database reconciliation protocol.

For DevOps and SRE teams, this charm will make operating Hockeypuck simple and straightforward through Juju's clean interface.

## In this documentation

| | |
|--|--|
|  [Tutorials](https://charmhub.io/hockeypuck-k8s/docs/tutorial-getting-started)</br>  Get started - a hands-on introduction to using the charm for new users </br> |  [How-to guides](https://charmhub.io/hockeypuck-k8s/docs/how-to-contribute) </br> Step-by-step guides covering key operations and common tasks |
| [Reference](https://charmhub.io/hockeypuck-k8s/docs/reference-actions) </br> Technical information - specifications, APIs, architecture | [Explanation](https://charmhub.io/hockeypuck-k8s/docs/explanation-charm-architecture) </br> Concepts - discussion and clarification of key topics  |

## Contributing to this documentation

Documentation is an important part of this project, and we take the same open-source approach to the documentation as 
the code. As such, we welcome community contributions, suggestions and constructive feedback on our documentation. 
Our documentation is hosted on the [Charmhub forum](https://discourse.charmhub.io/) 
to enable easy collaboration. Please use the "Help us improve this documentation" links on each documentation page to 
either directly change something you see that's wrong, ask a question or make a suggestion about a potential change via 
the comments section.

If there's a particular area of documentation that you'd like to see that's missing, please 
[file a bug](https://github.com/canonical/hockeypuck-k8s-operator/issues).

## Project and community

The Hockeypuck Kubernetes operator is a member of the Ubuntu family. It's an open-source project that warmly welcomes community 
projects, contributions, suggestions, fixes, and constructive feedback.

- [Code of conduct](https://ubuntu.com/community/code-of-conduct)
- [Get support](https://discourse.charmhub.io/)
- [Join our online chat](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)
- [Contribute](https://github.com/canonical/hockeypuck-k8s-operator/blob/main/CONTRIBUTING.md)

Thinking about using the Hockeypuck Kubernetes operator for your next project? 
[Get in touch](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)!

# Contents

1. [Changelog](changelog.md)
1. [Explanation](explanation)
  1. [Charm architecture](explanation/charm-architecture.md)
  1. [Security](explanation/security.md)
1. [How To](how-to)
  1. [Back up and restore](how-to/backup-and-restore-hockeypuck.md)
  1. [How to contribute](how-to/contribute.md)
  1. [Integrate with COS](how-to/integrate-with-cos.md)
  1. [Manage admin keys in Hockeypuck](how-to/manage-admin-keys.md)
  1. [Manage GPG keys](how-to/manage-gpg-keys.md)
  1. [Reconcile between two key servers](how-to/reconcile-between-two-keyservers.md)
  1. [Upgrade](how-to/upgrade.md)
1. [Reference](reference)
  1. [Actions](reference/actions.md)
  1. [Configurations](reference/configurations.md)
  1. [Integrations](reference/integrations.md)
  1. [Metrics](reference/metrics.md)
  1. [Hockeypuck ports](reference/ports.md)
1. [Tutorial](tutorial)
  1. [Deploy the Hockeypuck charm for the first time](tutorial/getting-started.md)