# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

locals {
  lxd_controller_address = "10.68.79.149:17070"
  lxd_controller_cert = <<EOT
-----BEGIN CERTIFICATE-----
MIIEEjCCAnqgAwIBAgIUQ/qXIQ1KpY6iOvWepLgBKFtRJBEwDQYJKoZIhvcNAQEL
BQAwITENMAsGA1UEChMESnVqdTEQMA4GA1UEAxMHanVqdS1jYTAeFw0yNTAzMTgx
NTA3MDdaFw0zNTAzMTgxNTEyMDdaMCExDTALBgNVBAoTBEp1anUxEDAOBgNVBAMT
B2p1anUtY2EwggGiMA0GCSqGSIb3DQEBAQUAA4IBjwAwggGKAoIBgQCixUizlpB3
QQgZcnjC8MHfG2sTAGd68yJf6nCO31wapluos9ke8ffprAk548rRFK2TeNxVwwpX
i2bRBCWG1R4//uVfku5Z5fwi3ycru4AFRdxmFPC/RyN1O/mxbIdjBn932omz+vgp
YBGHyO8MTeq3E8nDdgJRWH1+U/kz25NjPSnC/zHuJ9jTqu4JRx+7ku9y3I1Vakmv
+TN4bgnm91OOEntBPU1zIpCXEWICF0OAMWQrQVH9ol/8SybmToVbzN+KXtVeaep7
b+YbjcO7nowAxBQHMWL2fljKl0Vh1gU8eiBu0GLvGwe30ysoLAZDbymdL8W2l/gQ
BfYCqQ0HGMbuAVA5+Ein8CrKyVNy4VedcS7g9z6HLCnoqfeG3EJHljHu5jVrfsit
Aysyo2duRaBeGoCbyHrinyEXMeNYOzmJ7dIUqpIWUBStCE4k8cT13Geg3YDxNfTf
iY/iFKIN0FysEf8RW2mn+8pVC1fCxQRNKM/6yaJn48j2TsKDdNfBDm8CAwEAAaNC
MEAwDgYDVR0PAQH/BAQDAgKkMA8GA1UdEwEB/wQFMAMBAf8wHQYDVR0OBBYEFHWA
/aTHowrH98iEGVa8AKCELmvVMA0GCSqGSIb3DQEBCwUAA4IBgQCQrYlHkYJSkylk
GxOh9A3WLDVwHYrtfowXGK1yPDltkfRo+syJfahjxyD97exBscCO66f3wIpIOudI
UO0gtrUvKonVsVaZLhrMNurBgAwwqLb3bRitwZvC/aeprMCZE6P74BFZxYJ9VxG2
FcEyjUMtQvn24g2xTaYUzPgrRkUNjzmxgateczqPAj9ohREA3Fi98DD0L1aRbzS/
dZ+CkpoSAW1Kbfax7Qkg74viRLp7jfsMQVkqOCONAZHacvXg1vy5HRPMw7M1vEVM
msTbiAkUNkH6Lx35hRsxH4rMJmPb1XRME6oKk1zbJOL/oXi1NTeOyDnkyJOSMkvD
64lEFMZJuo8kRvO9KZ8EDfTK5nkNvHOQBaz+5nFfbkGr9MF7IeV/BnCfdrF5VmBq
g01Zc0Fxc2benmosvtxDsVIIFfquipDi5rKiJ8TvV3apQ1Zb2j+Tncpgmd1A1Ksr
5VR4aaxJMd47n3tbAg7vUwjqiY1k5CQZNwpwlkH56GELrymGyMI=
-----END CERTIFICATE-----
EOT
   k8s_controller_address = "10.152.183.78:17070"
   k8s_controller_cert = <<EOT
-----BEGIN CERTIFICATE-----
MIIEEjCCAnqgAwIBAgIUPRR7fPwuabBLcygJwNhTWmezStEwDQYJKoZIhvcNAQEL
BQAwITENMAsGA1UEChMESnVqdTEQMA4GA1UEAxMHanVqdS1jYTAeFw0yNTAxMjIx
MjAyMjRaFw0zNTAxMjIxMjA3MjRaMCExDTALBgNVBAoTBEp1anUxEDAOBgNVBAMT
B2p1anUtY2EwggGiMA0GCSqGSIb3DQEBAQUAA4IBjwAwggGKAoIBgQDC20gFFghB
V4inXOK/RdVD8gV5vJC+KcYC7ceNOGRZy1j+tawzmJxtbD3bADiD2MSzvRttat0E
s1xun/S6U4qICJ32pO6d7bjLYk+We7eRBR/TlbOD4JnGiWS7I19VjJ9nin9YZHXd
eKnYKmD0f6MWk5Po0Ar5PX0hEVE/CNhiNpiHdmYyyVvGYvlFu1jNOjCA9YH18WOy
OzqVjPwSrRKL25CI6R097bUoWzDcPLSzJythRMn6njPTy08QFgtUlIX7wgkbElfq
6BGf+pJk6bAEkZUxAMwI7elNaH9HRJLb/sRPzpAvtvaSFf60L3d2IKcwG3g7lUwF
t18TjVeFyF9rD/fsSnugahD2alndg61CVtusRoQsMRbBKtcw/yYdalU3LXGhNM28
zFZ2K05s9AuVmGDHDfvwdY5Zyb8/Pveblk8biwi0GmBq7pwXFuvjEHMEHNP7fXbe
K9U47yF+vpuWRXW/aMImQJtWUs1TUBuY+BtD8YWZmlGCdclt8rJj+WMCAwEAAaNC
MEAwDgYDVR0PAQH/BAQDAgKkMA8GA1UdEwEB/wQFMAMBAf8wHQYDVR0OBBYEFOgZ
e2O4QIhVm1jx9rzb97/+nvJ1MA0GCSqGSIb3DQEBCwUAA4IBgQCZC6tM/hMh7yej
ciFkVNDW6PhQsV2Dq9+1jktLEjnI/X0ls+2ASmXa+J2wBrGVnylCUVdKS3D1bKdb
GVg9WsCJJA/2LIzwmEcywv9Gsqkprrfsj0g9u8CFYoVjnhf2g8X1zir5VaTOVJqd
zb3bifGdWZMuchzV6X/nEwtzG0Txb34ZsnQiL5PucnFrJZx/vmnrNhZzSFc/p+Zz
qrZGlj7GhqPS7IMW7O3YD+SGnidjJXQWOMAUSVuxzmY7CPkQeRO5juACaIFXD6k0
D9ePMJqK8Iu7WksvFRXnRUpEIIF2+ItdMpKzsAblsWkZjTSCgCtbY1+EDBx+1ra5
HU//g6ti1mVb4/SJdHsm4WFx6UKJpsgw61dPt1HKAFCs9PUCCyfISMcJ8tR4+YwH
Tt0Xbaarrxkv1w+s1gHKGYhUnam0e2vQ5GQs07Rccb9j0jd5Qv9BAnB/FONjeBYm
4zuN8ulWha20K2OubZmHzthPwNfpovt0qCj4dTBW3DOeGyypADA=
-----END CERTIFICATE-----
EOT
}

provider "juju" {
  controller_addresses = local.k8s_controller_address
  ca_certificate       = local.k8s_controller_cert
  username             = "admin"
  password             = "test"
}


provider "juju" {
  alias = "hockeypuck_db"
  controller_addresses = local.lxd_controller_address
  ca_certificate       = local.lxd_controller_cert
  username             = "admin"                                            
  password             = "test"                                            
}

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
  revision    = var.hockeypuck.revision
  base        = var.hockeypuck.base
  units       = var.hockeypuck.units
}

module "postgresql" {
  source      = "git::https://github.com/canonical/postgresql-operator//terraform"
  app_name    = var.postgresql.app_name
  channel     = var.postgresql.channel
  config      = var.postgresql.config
  constraints = var.postgresql.constraints
  juju_model_name       = data.juju_model.hockeypuck_db.name
  revision    = var.postgresql.revision
  base        = var.postgresql.base
  units       = var.postgresql.units

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

resource "juju_offer" "postgresql" {
  model            = data.juju_model.hockeypuck_db.name
  application_name = module.postgresql.application_name
  endpoint         = module.postgresql.provides.database

  provider = juju.hockeypuck_db
}

resource "juju_integration" "hockeypuck_postgresql" {
  model = data.juju_model.hockeypuck.name

  application {
    name     = module.hockeypuck_k8s.app_name
    endpoint = module.hockeypuck_k8s.requires.postgresql
  }

  application {
    offer_url = juju_offer.postgresql.url
  }
}

resource "juju_integration" "hockeypuck_nginx" {
  model = data.juju_model.hockeypuck.name

  application {
    name     = module.hockeypuck_k8s.app_name
    endpoint = module.hockeypuck_k8s.requires.ingress
  }

  application {
    name     = module.nginx_ingress.app_name
    endpoint = module.nginx_ingress.provides.ingress
  }
}

resource "juju_integration" "hockeypuck_traefik" {
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

