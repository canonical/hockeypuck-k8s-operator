# Contributing

## Overview

This document explains the processes and practices recommended for contributing enhancements to the hockeypuck-k8s charm.

- Generally, before developing enhancements to this charm, you should consider [opening an issue
  ](https://github.com/canonical/hockeypuck-k8s-operator/issues) explaining your use case.
- If you would like to chat with us about your use-cases or proposed implementation, you can reach
  us at [Canonical Matrix public channel](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)
  or [Discourse](https://discourse.charmhub.io/).
- Familiarizing yourself with the [Charmed Operator Framework](https://documentation.ubuntu.com/juju/latest/howto/manage-charms/index.html#build-a-charm) library
  will help you a lot when working on new features or bug fixes.
- All enhancements require review before being merged. Code review typically examines
  - code quality
  - test coverage
  - user experience for Juju operators of this charm.
- Once your pull request is approved, we squash and merge your pull request branch onto
  the `main` branch. This creates a linear Git commit history.

## Developing

To make contributions to this charm, you'll need a working [development setup](https://documentation.ubuntu.com/juju/3.6/tutorial/#set-up-an-isolated-test-environment).

The code for this charm can be downloaded as follows:

```
git clone https://github.com/canonical/hockeypuck-k8s-operator.git
```

You can use the environments created by `tox` for development:

```shell
tox --notest -e unit
source .tox/unit/bin/activate
```

<!-- TODO: Check whether these instructions are more appropriate:
You can create an environment for development with `tox`:

```shell
tox devenv -e integration
source venv/bin/activate
```
-->

### Testing

This project uses `tox` for managing test environments. There are some pre-configured environments
that can be used for linting and formatting code when you're preparing contributions to the charm:

* `tox`: Runs all of the basic checks (`lint`, `unit`, `static`, and `coverage-report`).
* `tox -e fmt`: Runs formatting using `black` and `isort`.
* `tox -e lint`: Runs a range of static code analysis to check the code.
* `tox -e static`: Runs other checks such as `bandit` for security issues.
* `tox -e unit`: Runs the unit tests.
* `tox -e integration`: Runs the integration tests.

### Building the charm

Build the charm in this git repository using:

```shell
charmcraft pack
```

For the integration tests (and also to deploy the charm locally), the hockeypuck
image is required in the microk8s registry. To enable it, run:

```shell
microk8s enable registry
```

The following commands push the image into the registry:

```shell
cd [project_dir]/hockeypuck_rock && rockcraft pack
rockcraft.skopeo --insecure-policy copy --dest-tls-verify=false oci-archive:hockeypuck_0.2_amd64.rock docker://localhost:32000/hockeypuck:0.2
```

### Deploying

<!-- TODO: Determine if the juju deploy command should be updated -->

```bash
# Create a model
juju add-model hockeypuck-test
# Enable DEBUG logging
juju model-config logging-config="<root>=INFO;unit=DEBUG"
# Deploy the charm (assuming you're on amd64)
juju deploy ./hockeypuck-k8s_amd64.charm --resource app-image=localhost:32000/hockeypuck:0.2 --config metrics-port=9626 --config app-port=11371
```

## Canonical Contributor Agreement

Canonical welcomes contributions to the hockeypuck-k8s charm. Please check out our [contributor agreement](https://ubuntu.com/legal/contributors) if you're interested in contributing to the solution.
