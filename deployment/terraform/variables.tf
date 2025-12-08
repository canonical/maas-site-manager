variable "s3_access_key" {
  description = "Access key used to access the S3 bucket"
  type        = string
}

variable "s3_secret_key" {
  description = "Secret key used to access the S3 bucket"
  type        = string
  sensitive   = true
}

variable s3_endpoint {
  description = "S3 storage host"
  type        = string
}

variable "s3_bucket" {
  description = "Bucket name to store images in"
  type        = string
  default     = "msm-images"
}

variable s3_path {
  description = "Path to store images in"
  type        = string
  default     = "/"
}

variable "maas_site_manager_channel" {
  description = "Channel to deploy the MAAS Site Manager charm from"
  type        = string
  default     = "latest/edge"
}

variable "maas_site_manager_revision" {
  description = "Revision to use for the MAAS Site Manager charm"
  type        = number
  nullable    = true
  default     = null
}

variable "postgresql_channel" {
  description = "Channel to deploy the Postgresql charm from"
  type        = string
  default     = "14/stable"
}

variable "postgresql_revision" {
  description = "Revision to use for the Postgresql charm"
  type        = number
  nullable    = true
  default     = null
}

variable "s3_integrator_channel" {
  description = "Channel to deploy the s3-integrator charm from"
  type        = string
  default     = "latest/stable"
}

variable "s3_integrator_revision" {
  description = "Revision to use for the s3-integrator charm"
  type        = number
  nullable    = true
  default     = null
}

variable "traefik_channel" {
  description = "Channel to deploy the traefik charm from"
  type        = string
  default     = "latest/stable"
}

variable "traefik_revision" {
  description = "Revision to use for the traefik charm"
  type        = number
  nullable    = true
  default     = null
}

variable "temporal_server_channel" {
  description = "Channel to deploy the temporal-k8s charm from"
  type        = string
  default     = "latest/stable"
}

variable "temporal_server_revision" {
  description = "Revision to use for the temporal-k8s charm"
  type        = number
  nullable    = true
  default     = null
}

variable "temporal_admin_channel" {
  description = "Channel to deploy the temporal-admin-k8s charm from"
  type        = string
  default     = "latest/stable"
}

variable "temporal_admin_revision" {
  description = "Revision to use for the temporal-admin-k8s charm"
  type        = number
  nullable    = true
  default     = null
}

variable "temporal_worker_channel" {
  description = "Channel to deploy the temporal-worker-k8s charm from"
  type        = string
  default     = "latest/stable"
}

variable "temporal_worker_revision" {
  description = "Revision to use for the temporal-worker-k8s charm"
  type        = number
  nullable    = true
  default     = null
}

variable temporal_worker_resources {
  description = "OCI Image resource for temporal worker"
  type        = map
  default     = {temporal-worker-image:"ghcr.io/canonical/maas-site-manager:0.1"}
}

variable "juju_cloud_name" {
  description = "Name of the Juju cloud to use"
  type        = string
  default     = "microk8s"
}

variable "s3_offer_url" {
  description = "Offer url for s3-integrator charm"
  type        = string
  nullable    = true
  default     = null
}

variable postgresql_offer_url {
  description = "Offer url for PostgreSQL charm"
  type        = string
  nullable    = true
  default     = null
}

variable "ingress_offer_url" {
  description = "Offer url for ingress relation interface"
  type        = string
  nullable    = true
  default     = null
}

variable "logging_consumer_offer_url" {
  description = "Offer url for logging-consumer:loki_push_api relation interface"
  type        = string
  nullable    = true
  default     = null
}
variable "metrics_endpoint_offer_url" {
  description = "Offer url for metrics-endpoint:prometheus_scrape relation interface"
  type        = string
  nullable    = true
  default     = null
}
variable "grafana_dashboard_offer_url" {
  description = "Offer url for grafana-dashboard relation interface"
  type        = string
  nullable    = true
  default     = null
}

variable "temporal_server_offer_url" {
  description = "Offer url for temporal server host_info relation interface"
  type        = string
  nullable    = true
  default     = null
}

variable "temporal_worker_offer_url" {
  description = "Offer url for temporal worker relation interface"
  type        = string
  nullable    = true
  default     = null
}

variable "temporal_namespace" {
  description = "Namespace for temporal worker"
  type        = string
  default     = "msm-namespace"
}

variable "temporal_task_queue" {
  description = "Task queue for temporal worker"
  type        = string
  default     = "msm-queue"
}
