# Terraform modules

This project contains the [Terraform][Terraform] modules to deploy the 
[Hockeypuck charm][Hockeypuck charm] with its dependencies.

The modules use the [Terraform Juju provider][Terraform Juju provider] to model
the bundle deployment onto any Kubernetes environment managed by [Juju][Juju].

## Module structure

- **main.tf** - Defines the Juju application to be deployed.
- **variables.tf** - Allows customization of the deployment including Juju model name, charm's channel and configuration.
- **output.tf** - Responsible for integrating the module with other Terraform modules, primarily by defining potential integration endpoints (charm integrations).
- **versions.tf** - Defines the Terraform provider.

[Terraform]: https://www.terraform.io/
[Terraform Juju provider]: https://registry.terraform.io/providers/juju/juju/latest
[Juju]: https://juju.is
[Hockeypuck charm]: https://charmhub.io/hockeypuck

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_juju"></a> [juju](#requirement\_juju) | >= 0.17.1 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_juju"></a> [juju](#provider\_juju) | >= 0.17.1 |
| <a name="provider_juju.hockeypuck_db"></a> [juju.hockeypuck\_db](#provider\_juju.hockeypuck\_db) | >= 0.17.1 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_hockeypuck_k8s"></a> [hockeypuck\_k8s](#module\_hockeypuck\_k8s) | ../charm | n/a |
| <a name="module_postgresql"></a> [postgresql](#module\_postgresql) | git::https://github.com/canonical/postgresql-operator//terraform | n/a |
| <a name="module_traefik_k8s"></a> [traefik\_k8s](#module\_traefik\_k8s) | ./modules/traefik-k8s | n/a |

## Resources

| Name | Type |
|------|------|
| [juju_access_offer.postgresql](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/access_offer) | resource |
| [juju_integration.hockeypuck_postgresql_database](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.hockeypuck_traefik_nginx](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.hockeypuck_traefik_traefik_route](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_offer.postgresql](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/offer) | resource |
| [juju_model.hockeypuck](https://registry.terraform.io/providers/juju/juju/latest/docs/data-sources/model) | data source |
| [juju_model.hockeypuck_db](https://registry.terraform.io/providers/juju/juju/latest/docs/data-sources/model) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_db_model"></a> [db\_model](#input\_db\_model) | Reference to the VM Juju model to deploy database charm to. | `string` | n/a | yes |
| <a name="input_db_model_user"></a> [db\_model\_user](#input\_db\_model\_user) | Juju user used for deploying database charms. | `string` | n/a | yes |
| <a name="input_hockeypuck"></a> [hockeypuck](#input\_hockeypuck) | n/a | <pre>object({<br/>    app_name    = optional(string, "hockeypuck-k8s")<br/>    channel     = optional(string, "2.2/edge")<br/>    config      = optional(map(string), { "metrics-port" : 9626, "app-port" : 11371 })<br/>    constraints = optional(string, "arch=amd64")<br/>    revision    = optional(number)<br/>    base        = optional(string, "ubuntu@24.04")<br/>    units       = optional(number, 1)<br/>  })</pre> | n/a | yes |
| <a name="input_model"></a> [model](#input\_model) | Reference to the k8s Juju model to deploy application to. | `string` | n/a | yes |
| <a name="input_model_user"></a> [model\_user](#input\_model\_user) | Juju user used for deploying the application. | `string` | n/a | yes |
| <a name="input_postgresql"></a> [postgresql](#input\_postgresql) | n/a | <pre>object({<br/>    app_name    = optional(string, "postgresql")<br/>    channel     = optional(string, "14/stable")<br/>    config      = optional(map(string), {})<br/>    constraints = optional(string, "arch=amd64")<br/>    revision    = optional(number)<br/>    base        = optional(string, "ubuntu@22.04")<br/>    units       = optional(number, 1)<br/>  })</pre> | n/a | yes |
| <a name="input_traefik_k8s"></a> [traefik\_k8s](#input\_traefik\_k8s) | n/a | <pre>object({<br/>    app_name    = optional(string, "traefik-k8s")<br/>    channel     = optional(string, "latest/stable")<br/>    config      = optional(map(string), {})<br/>    constraints = optional(string, "arch=amd64")<br/>    revision    = optional(number)<br/>    base        = optional(string, "ubuntu@20.04")<br/>    units       = optional(number, 1)<br/>    storage     = optional(map(string), {})<br/>  })</pre> | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_app_name"></a> [app\_name](#output\_app\_name) | Name of the deployed application. |
| <a name="output_provides"></a> [provides](#output\_provides) | n/a |
| <a name="output_requires"></a> [requires](#output\_requires) | n/a |
<!-- END_TF_DOCS -->