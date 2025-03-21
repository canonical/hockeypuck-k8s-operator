# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

data "juju_model" "hockeypuck" {
  name = var.model
}

data "juju_model" "hockeypuck_db" {
  name = var.db_model

  provider = juju.hockeypuck_db
}

module "hockeypuck_k8s" {
  source      = "../charm"
  app_name    = var.hockeypuck.app_name
  channel     = var.hockeypuck.channel
  config      = var.hockeypuck.config
  model       = data.juju_model.hockeypuck.name
  constraints = var.hockeypuck.constraints
  revision    = var.hockeypuck.revision
  base        = var.hockeypuck.base
  units       = var.hockeypuck.units
}

module "postgresql" {
  source          = "git::https://github.com/canonical/postgresql-operator//terraform"
  app_name        = var.postgresql.app_name
  channel         = var.postgresql.channel
  config          = var.postgresql.config
  constraints     = var.postgresql.constraints
  juju_model_name = data.juju_model.hockeypuck_db.name
  revision        = var.postgresql.revision
  base            = var.postgresql.base
  units           = var.postgresql.units

  providers = {
    juju = juju.hockeypuck_db
  }
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

resource "juju_offer" "postgresql" {
  model            = data.juju_model.hockeypuck_db.name
  application_name = module.postgresql.application_name
  endpoint         = module.postgresql.provides.database

  provider = juju.hockeypuck_db
}

resource "juju_access_offer" "postgresql" {
  offer_url = juju_offer.postgresql.url
  admin     = [var.db_model_user]
  consume   = [var.model_user]

  provider = juju.hockeypuck_db
}

resource "juju_integration" "hockeypuck_postgresql_database" {
  model = data.juju_model.hockeypuck.name

  application {
    name     = module.hockeypuck_k8s.app_name
    endpoint = module.hockeypuck_k8s.requires.postgresql
  }

  application {
    offer_url = juju_offer.postgresql.url
  }
}

resource "juju_integration" "hockeypuck_traefik_nginx" {
  model = data.juju_model.hockeypuck.name

  application {
    name     = module.hockeypuck_k8s.app_name
    endpoint = module.hockeypuck_k8s.requires.ingress
  }

  application {
    name     = module.traefik_k8s.app_name
    endpoint = module.traefik_k8s.provides.ingress
  }
}

resource "juju_integration" "hockeypuck_traefik_traefik_route" {
  model = data.juju_model.hockeypuck.name

  application {
    name     = module.hockeypuck_k8s.app_name
    endpoint = module.hockeypuck_k8s.requires.traefik_route
  }

  application {
    name     = module.traefik_k8s.app_name
    endpoint = module.traefik_k8s.provides.traefik_route
  }
}
