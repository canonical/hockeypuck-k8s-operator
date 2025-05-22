# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

variable "app_name" {
  description = "Name of the application in the Juju model."
  type        = string
  default     = "hockeypuck-k8s"
}

variable "channel" {
  description = "The channel to use when deploying a charm."
  type        = string
  default     = "2.2/edge"
}

variable "config" {
  description = "Application config. Details about available options can be found at https://charmhub.io/hockeypuck-k8s/configurations."
  type        = map(string)
  default     = { "metrics-port" : 9626, "app-port" : 11371 }
}

variable "constraints" {
  description = "Juju constraints to apply for this application."
  type        = string
  default     = ""
}

variable "model" {
  description = "Reference to a `juju_model`."
  type        = string
  default     = ""
}

variable "revision" {
  description = "Revision number of the charm"
  type        = number
  default     = null
}

variable "base" {
  description = "The operating system on which to deploy"
  type        = string
  default     = "ubuntu@24.04"
}

variable "units" {
  description = "Number of units to deploy"
  type        = number
  default     = 1
}
