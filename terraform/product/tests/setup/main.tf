# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

terraform {
  required_version = "~> 1.12"
  required_providers {
    juju = {
      version = "~> 1.0"
      source  = "juju/juju"
    }
  }
}

provider "juju" {}

resource "juju_model" "test_model" {
  name = "tf-hockeypuck-k8s-${formatdate("YYYYMMDDhhmmss", timestamp())}"
}

resource "juju_model" "test_db_model" {
  name = "tf-hockeypuck-db-${formatdate("YYYYMMDDhhmmss", timestamp())}"
}

output "model_uuid" {
  value = juju_model.test_model.uuid
}

output "db_model_uuid" {
  value = juju_model.test_db_model.uuid
}
