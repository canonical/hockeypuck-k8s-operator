# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

variable "model" {
  description = "Reference to the k8s Juju model to deploy application to."
  type        = string
}

variable "db_model" {
  description = "Reference to the VM Juju model to deploy database charm to."
  type        = string
}

variable "model_user" {
  description = "Juju user used for deploying the application."
  type        = string
}

variable "db_model_user" {
  description = "Juju user used for deploying database charms."
  type        = string
}

variable "hockeypuck" {
  type = object({
    app_name    = optional(string, "hockeypuck")
    channel     = optional(string, "latest/edge")
    config      = optional(map(string), {})
    constraints = optional(string, "arch=amd64")
    revision    = optional(number)
    base        = optional(string, "ubuntu@24.04")
    units       = optional(number, 1)
  })
}

variable "postgresql_k8s" {
  type = object({
    app_name    = optional(string, "postgresql-k8s")
    channel     = optional(string, "14/stable")
    config      = optional(map(string), {})
    constraints = optional(string, "arch=amd64")
    revision    = optional(number)
    base        = optional(string, "ubuntu@24.04")
    units       = optional(number, 1)
  })
}

variable "nginx_ingress" {
  type = object({
    app_name    = optional(string, "nginx-ingress-integrator")
    channel     = optional(string, "latest/stable")
    config      = optional(map(string), {})
    constraints = optional(string, "arch=amd64")
    revision    = optional(number)
    base        = optional(string, "ubuntu@22.04")
    units       = optional(number, 1)
  })
}

variable "traefik_k8s" {
  type = object({
    app_name    = optional(string, "traefik-k8s")
    channel     = optional(string, "latest/stable")
    config      = optional(map(string), {})
    constraints = optional(string, "arch=amd64")
    revision    = optional(number)
    base        = optional(string, "ubuntu@20.04")
    units       = optional(number, 1)
    storage     = optional(map(string), {})
  })
}