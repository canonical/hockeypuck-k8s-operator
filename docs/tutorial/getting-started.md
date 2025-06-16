# Deploy the Hockeypuck charm for the first time

## What you'll do

- Deploy the [Hockeypuck charm](https://charmhub.io/hockeypuck-k8s)
- Access the Hockeypuck web UI

By the end of this tutorial, you’ll have a working Hockeypuck server running on a Kubernetes cluster managed by Juju.

### What you'll need

- A machine with amd64 architecture.
- Juju 3.x installed.
- Juju MicroK8s controller created and active named `microk8s`, with the [MetalLB add-on](https://microk8s.io/docs/addon-metallb) enabled (required for Traefik ingress to work).

[note]
All the requirements can be met using the [Multipass charm-dev blueprint](https://documentation.ubuntu.com/juju/3.6/howto/manage-your-deployment/manage-your-deployment-environment/#set-things-up). Use the Multipass VM shell to run all commands in this tutorial.
[/note]

For more information about how to install Juju, see [Get started with Juju](https://documentation.ubuntu.com/juju/3.6/tutorial/).

### Set up a tutorial model

To easily clean up the resources and to separate your workload from the contents of this tutorial,
set up a new Juju model in the `microk8s` controller with the following command.

```bash
juju switch microk8s
juju add-model hockeypuck-tutorial
```

### Deploy the Hockeypuck charm

Deploy the Hockeypuck charm and PostgreSQL charm, and integrate them.

```bash
juju deploy hockeypuck-k8s --channel=2.2/edge --config metrics-port=9626 --config app-port=11371
juju deploy postgresql-k8s --channel 14/stable --trust
juju integrate hockeypuck-k8s postgresql-k8s
```

Wait for the charm to be active:
```bash
juju wait-for application hockeypuck-k8s
```

[note]
The Hockeypuck application supports only a single unit. Adding more units through the `--num-units`
flag will result in the application entering a blocked state. To achieve redundancy, 
deploy multiple independent instances of Hockeypuck and [configure peering](https://charmhub.io/hockeypuck-k8s/docs/how-to-reconcile-between-two-keyservers) between them.
[/note]

### Expose Hockeypuck webserver through ingress

Deploy the Traefik charm and integrate it with the Hockeypuck charm:
```bash
juju deploy traefik-k8s --channel=latest/edge --trust
juju integrate hockeypuck-k8s:ingress traefik-k8s
```

[note]
The Traefik charm must be deployed on the same Kubernetes cluster as Hockeypuck charm.
[/note]

You can check the status with:
```bash
juju status --relations
```

After a few minutes, the deployment will be finished and all the units should be in 
the active status.

Run the following command to retrieve the URL for the Hockeypuck UI:
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

Congratulations! You have successfully finished the Hockeypuck charm tutorial. You can now remove the
model environment that you’ve created using the following command.


```bash
juju destroy-model hockeypuck-tutorial --destroy-storage
```
