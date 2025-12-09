resource "juju_model" "development" {
  name = "msm"
  cloud {
    name = var.juju_cloud_name
  }
}

resource "juju_application" "msm" {
  name = "maas-site-manager-k8s"
  model = juju_model.development.name

  charm {
    name = "maas-site-manager-k8s"
    channel = var.maas_site_manager_channel
    revision = var.maas_site_manager_revision
  }

  # temporal-server-address will be configured later
  config = {
    temporal-namespace = var.temporal_namespace
    temporal-task-queue = var.temporal_task_queue
  }
  resources = {
    site-manager-image = "ghcr.io/canonical/maas-site-manager:0.1"
  }

  units = 1
  lifecycle {
    ignore_changes = [
      config["temporal-server-address"],
    ]
  }
}

resource "juju_application" "postgresql" {
  name = "postgresql-k8s"
  model = juju_model.development.name
  trust = true
  count = var.postgresql_offer_url == null ? 1 : 0

  charm {
    name = "postgresql-k8s"
    channel = var.postgresql_channel
    revision = var.postgresql_revision
  }

  units = 1
}


resource "juju_application" "s3" {
  name = "s3-integrator"
  model = juju_model.development.name
  count = var.s3_offer_url == null ? 1 : 0


  charm {
    name = "s3-integrator"
    channel = var.s3_integrator_channel
    revision = var.s3_integrator_revision
  }

  units = 1
  config = {
    bucket = var.s3_bucket
    path = var.s3_path
    endpoint = var.s3_endpoint
  }

  provisioner "local-exec" {
    # This is needed until we move to 2/edge s3-integration where the access-key and secret-key are
    # set with a Juju secret.
    command = (<<-EOT
      juju wait-for application -m ${self.model} ${self.name} --timeout 3600s \
        --query='forEach(units, unit => unit.workload-status == "blocked" && unit.agent-status=="idle")'

      juju run -m ${self.model} ${self.name}/leader sync-s3-credentials \
        access-key=${var.s3_access_key} \
        secret-key=${var.s3_secret_key}
    EOT
    )
  }
}

resource "juju_application" "traefik" {
  name = "traefik-k8s"
  model = juju_model.development.name
  trust = true
  count = var.ingress_offer_url == null ? 1 : 0

  charm {
    name = "traefik-k8s"
    channel = var.traefik_channel
    revision = var.traefik_revision
  }

  units = 1
}


resource "juju_integration" "msm_to_postgresql" {
  model = juju_model.development.name

  application {
    name = juju_application.msm.name
  }

  dynamic "application" {
    for_each = juju_application.postgresql
    content {
      name = application.value.name
    }
  }

  dynamic "application" {
    for_each = compact([var.postgresql_offer_url])
    content {
      offer_url = application.value
    }
  }
}

resource "juju_offer" "postgresql" {
  model            = juju_model.development.name
  application_name = juju_application.postgresql[0].name
  endpoints         = ["database"]

  count = var.postgresql_offer_url == null && var.temporal_server_offer_url == null ? 1 : 0
}


resource "juju_integration" "msm_to_s3" {
  model = juju_model.development.name

  application {
    name = juju_application.msm.name
  }

  dynamic "application" {
    for_each = juju_application.s3
    content {
      name = application.value.name
    }
  }

  dynamic "application" {
    for_each = compact([var.s3_offer_url])
    content {
      offer_url = application.value
    }
  }
}

resource "juju_integration" "msm_to_ingress" {
  model = juju_model.development.name

  application {
    name = juju_application.msm.name
  }

  dynamic "application" {
    for_each = juju_application.traefik
    content {
      name = application.value.name
    }
  }

  dynamic "application" {
    for_each = compact([var.ingress_offer_url])
    content {
      offer_url = application.value
    }
  }
}

resource "juju_integration" "msm_to_loki" {
  model = juju_model.development.name
  count = var.logging_consumer_offer_url != null ? 1 : 0

  application {
    name = juju_application.msm.name
  }

  application {
    offer_url = var.logging_consumer_offer_url
  }
}

resource "juju_integration" "msm_to_prometheus" {
  model = juju_model.development.name
  count = var.metrics_endpoint_offer_url != null ? 1 : 0

  application {
    name = juju_application.msm.name
  }

  application {
    offer_url = var.metrics_endpoint_offer_url
  }
}

resource "juju_integration" "msm_to_grafana" {
  model = juju_model.development.name
  count = var.grafana_dashboard_offer_url != null ? 1 : 0

  application {
    name = juju_application.msm.name
  }

  application {
    offer_url = var.grafana_dashboard_offer_url
  }
}
