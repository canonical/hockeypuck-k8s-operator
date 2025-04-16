# Deploy the hockeypuck-k8s charm for the first time

## What you'll do

- Deploy the [hockeypuck-k8s charm](https://charmhub.io/hockeypuck-k8s)
- Access the Hockeypuck web UI

By the end, you’ll have a working Hockeypuck server running on a Kubernetes cluster managed by Juju.

### Requirements

- A machine with amd64 architecture.
- Juju 3.x installed.
- Juju MicroK8s controller created and active named `microk8s`, with the [MetalLB addon](https://microk8s.io/docs/addon-metallb) enabled (required for Traefik ingress to work)

> All the requirements can be met using the [Multipass charm-dev blueprint](https://juju.is/docs/juju/set-up--tear-down-your-test-environment#heading--set-up---tear-down-automatically). Use the Multipass VM shell to run all commands in this tutorial.

For more information about how to install Juju, see [Get started with Juju](https://juju.is/docs/olm/get-started-with-juju).

### Set up a tutorial model

To easily clean up the resources and to separate your workload from the contents of this tutorial,
set up a new Juju model in the `microk8s` controller with the following command.

```bash
juju switch microk8s
juju add-model hockeypuck-tutorial
```

### Deploy the hockeypuck-k8s charm

Deploy the hockeypuck-k8s charm, postgresql-k8s charm and relate them.

```bash
juju deploy hockeypuck-k8s --channel=2.2/edge --config metrics-port=9626 app-port=11371
juju deploy postgresql-k8s --channel 14/stable --trust
juju integrate hockeypuck-k8s postgresql-k8s
```

Wait for the charm to be active:
```bash
juju wait-for application hockeypuck-k8s
```

> **Note**: The hockeypuck application only supports a single unit. Adding more units through `--num-units`
flag will cause the application to be blocked.

### Expose Hockeypuck webserver through ingress

Deploy the traefik-k8s charm and integrate it with the Hockeypuck charm:
```bash
juju deploy traefik-k8s --channel=latest/edge --trust
juju integrate hockeypuck-k8s:ingress traefik-k8s
```

> **Note**: traefik-k8s must be deployed on the same k8s cluster as hockeypuck-k8s charm.

You can check the status with:
```bash
juju status --relations
```

After a few minutes, the deployment will be finished and all the units should be in 
the active status.

Run the following command to retrieve the URL for hockeypuck UI:
```bash
juju run traefik-k8s/0 show-proxied-endpoints --format=yaml
```

The output will be something similar to:
```bash
Running operation 1 with 1 task
  - task 2 on unit-traefik-k8s-0

Waiting for task 2...
traefik-k8s/0: 
  id: "2"
  results: 
    proxied-endpoints: '{"traefik-k8s": {"url": "http://10.12.97.102"}, "hockeypuck-k8s":
      {"url": "http://10.12.97.102/hockeypuck-tutorial-hockeypuck-k8s"}}'
    return-code: 0
  status: completed
  timing: 
    completed: 2024-09-27 15:09:36 +0200 CEST
    enqueued: 2024-09-27 15:09:35 +0200 CEST
    started: 2024-09-27 15:09:35 +0200 CEST
  unit: traefik-k8s/0
```

In this example, the URL to use in your browser will be `http://10.12.97.102/hockeypuck-tutorial-hockeypuck-k8s`. 
The exact IP address may differ depending on your environment. You can now access your Hockeypuck server UI at this URL.

### Cleaning up the environment

Congratulations! You have successfully finished the hockeypuck-k8s tutorial. You can now remove the
model environment that you’ve created using the following commands.


```bash
juju destroy-model hockeypuck-tutorial --destroy-storage
```
