# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

provider "juju" {}

provider "juju" {
  alias = "hockeypuck_db"
}

run "setup_tests" {
  module {
    source = "./tests/setup"
  }
}

run "basic_deploy" {
  command = plan

  variables {
    model_uuid    = run.setup_tests.model_uuid
    db_model_uuid = run.setup_tests.db_model_uuid
    model_user    = "admin"
    db_model_user = "admin"

    hockeypuck = {
      # renovate: depName="hockeypuck-k8s"
      revision = 6
    }

    postgresql = {
      # renovate: depName="postgresql"
      revision = 1061
    }

    traefik_k8s = {
      # renovate: depName="traefik-k8s"
      revision = 273
    }
  }

  assert {
    condition     = output.app_name == "hockeypuck-k8s"
    error_message = "hockeypuck-k8s app_name did not match expected"
  }
}
