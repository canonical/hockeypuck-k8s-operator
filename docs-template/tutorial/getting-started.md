# Deploy the hockeypuck-k8s charm for the first time

## What you'll do

- Deploy the [hockeypuck-k8s charm](https://charmhub.io/hockeypuck-k8s)
- Access the UI

This tutorial will walk through each step of deployment to get Hockeypuck up and running.

### Requirements

- A machine with amd64 architecture.
- Juju 3 installed.
- Juju MicroK8s controller created and active named `microk8s`. [MetalLB addon](https://microk8s.io/docs/addon-metallb) should be enabled for traefik-k8s to work.

> All the requirements can be met using the [Multipass charm-dev blueprint](https://juju.is/docs/juju/set-up--tear-down-your-test-environment#heading--set-up---tear-down-automatically). Use the Multipass VM shell to run all commands in this tutorial.

For more information about how to install Juju, see [Get started with Juju](https://juju.is/docs/olm/get-started-with-juju).

### Set up the tutorial model

To easily clean up the resources and to separate your workload from the contents of this tutorial,
set up a new Juju model in the `microk8s` controller with the following command.

```
juju switch microk8s
juju add-model hockeypuck-tutorial
```

### Deploy the hockeypuck-k8s charm

Start off by deploying the hockeypuck-k8s charm, postgresql-k8s charm and integrating the two 
applications.

```
juju deploy hockeypuck-k8s --channel=2.2/edge --config metrics-port=9626 app-port=11371
juju deploy postgresql-k8s --channel 14/stable --trust
juju integrate hockeypuck-k8s postgresql-k8s
```

Wait for the charm to be active:
```
juju wait-for application hockeypuck-k8s
```

The hockeypuck application can only have a single unit. Adding more units through `--num-units`
parameter will cause the application to be blocked.


### Expose hockeypuck-k8s through ingress

Deploy traefik-k8s charm and integrate it with the hockeypuck-k8s charm:
```
juju deploy traefik-k8s --channel=latest/edge --trust
juju integrate hockeypuck-k8s:ingress traefik-k8s
```

> Note: traefik-k8s must be deployed on the same k8s cluster as hockeypuck-k8s charm.

You can check the status with:
```
juju status --relations
```

After a few minutes, the deployment will be finished and all the units should be in 
the active status.

Run the following command to get the URL to view hockeypuck UI:
```
juju run traefik-k8s/0 show-proxied-endpoints --format=yaml
```

The output will be something similar to:
```
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

In this case, the URL to use in your browser will be `http://10.12.97.102/hockeypuck-tutorial-hockeypuck-k8s`. In
your case it will probably be a different IP address. You can now access your hockeypuck server UI at this URL.

### Cleaning up the environment

Congratulations! You have successfully finished the hockeypuck-k8s tutorial. You can now remove the
model environment that you’ve created using the following commands.


```
juju destroy-model hockeypuck-tutorial --destroy-storage
```
