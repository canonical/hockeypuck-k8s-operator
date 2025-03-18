# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

data "juju_model" "hockeypuck" {
  name = var.model
}

data "juju_model" "hockeypuck_db" {
  name = var.db_model

  provider = juju.hockeypuck_db
}

module "hockeypuck" {
  source      = "../charm"
  app_name    = var.hockeypuck.app_name
  channel     = var.hockeypuck.channel
  config      = var.hockeypuck.config
  model       = data.juju_model.hockeypuck.name
  revision    = var.hockeypuck.revision
  base        = var.hockeypuck.base
  units       = var.hockeypuck.units
}

module "postgresql_k8s" {
  source      = "git::https://github.com/canonical/postgresql-k8s-operator//terraform"
  app_name    = var.postgresql_k8s.app_name
  channel     = var.postgresql_k8s.channel
  config      = var.postgresql_k8s.config
  constraints = var.postgresql_k8s.constraints
  juju_model_name       = data.juju_model.hockeypuck_db.name
  revision    = var.postgresql_k8s.revision
  base        = var.postgresql_k8s.base
  units       = var.postgresql_k8s.units

  providers = {
    juju = juju.hockeypuck_db
  }
}

module "nginx_ingress" {
  source      = "./modules/nginx-ingress-integrator"
  app_name    = var.nginx_ingress.app_name
  channel     = var.nginx_ingress.channel
  config      = var.nginx_ingress.config
  constraints = var.nginx_ingress.constraints
  model       = data.juju_model.hockeypuck.name
  revision    = var.nginx_ingress.revision
  base        = var.nginx_ingress.base
  units       = var.nginx_ingress.units
}

module "traefik_k8s" {
  source      = "./modules/traefik-k8s"
  app_name    = var.traefik_k8s.app_name
  channel     = var.traefik_k8s.channel
  config      = var.traefik_k8s.config
  constraints = var.traefik_k8s.constraints
  model       = data.juju_model.hockeypuck.name
  revision    = var.traefik_k8s.revision
  base        = var.traefik_k8s.base
  units       = var.traefik_k8s.units
}

resource "juju_offer" "postgresql_k8s" {
  model            = data.juju_model.hockeypuck_db.name
  application_name = module.postgresql_k8s.app_name
  endpoint         = module.postgresql_k8s.provides.database

  provider = juju.hockeypuck_db
}

resource "juju_access_offer" "postgresql_k8s" {
  offer_url = juju_offer.postgresql_k8s.url
  admin     = [var.db_model_user]
  consume   = [var.model_user]

  provider = juju.hockeypuck_db
}

resource "juju_integration" "hockeypuck_postgres" {
  model = data.juju_model.hockeypuck.name

  application {
    name     = module.hockeypuck.app_name
    endpoint = module.hockeypuck.requires.postgresql
  }

  application {
    offer_url = juju_offer.postgresql_k8s.url
  }
}

resource "juju_integration" "hockeypuck_nginx" {
  model = data.juju_model.hockeypuck.name

  application {
    name     = module.hockeypuck.app_name
    endpoint = module.hockeypuck.requires.ingress
  }

  application {
    name     = module.nginx_ingress
    endpoint = module.nginx_ingress.provides.ingress
  }
}

resource "juju_integration" "hockeypuck_traefik" {
  model = data.juju_model.hockeypuck.name

  application {
    name     = module.hockeypuck.app_name
    endpoint = module.hockeypuck.requires.traefik_route
  }

  application {
    name     = module.traefik_k8s.app_name
    endpoint = module.traefik_k8s.provides.traefik_route
  }
}

