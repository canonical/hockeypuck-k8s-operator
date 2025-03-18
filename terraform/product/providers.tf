provider "juju" {
  alias          	= "opencti_db"
  controller_addresses = "juju-controller-36-staging-ps6.dynamic.admin.canonical.com:17070"
  ca_certificate   	= data.vault_generic_secret.juju_controller_certificate.data["ca_cert"]
  username        	= data.vault_generic_secret.juju_credentials_stg_opencti_db.data["username"]
  password        	= data.vault_generic_secret.juju_credentials_stg_opencti_db.data["password"]
}