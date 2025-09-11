resource "juju_model" "temporal" {
  name = "temporal"
  cloud {
    name = var.juju_cloud_name
  }
  count = var.temporal_server_offer_url == null ? 1 : 0
}


resource "juju_application" "temporal_server" {
  name = "temporal-k8s"
  count = var.temporal_server_offer_url == null ? 1 : 0
  model = juju_model.temporal[0].name
  units = 1
  charm {
    name = "temporal-k8s"
    channel = var.temporal_server_channel
    revision = var.temporal_server_revision
  }
  config = {
    num-history-shards = 4
  }
}

resource "juju_application" "temporal_admin" {
  name = "temporal-admin-k8s"
  count = var.temporal_server_offer_url == null ? 1 : 0
  model = juju_model.temporal[0].name
  units = 1
  charm {
    name = "temporal-admin-k8s"
    channel = var.temporal_admin_channel
    revision = var.temporal_admin_revision
  }
}



resource "juju_integration" "temporal_visibility_to_db" {
  count = var.temporal_server_offer_url == null ? 1 : 0
  model = juju_model.temporal[0].name
  application {
    name = juju_application.temporal_server[0].name
    endpoint = "visibility"
  }

  dynamic "application" {
    for_each = juju_offer.postgresql
    content {
      offer_url = juju_offer.postgresql[0].url
    }
  }

  dynamic "application" {
    for_each = compact([var.postgresql_offer_url])
    content {
      offer_url = application.value
    }
  }
}


resource "juju_integration" "temporal_db_to_db" {
  count = var.temporal_server_offer_url == null ? 1 : 0
  model = juju_model.temporal[0].name

  application {
    name = juju_application.temporal_server[0].name
    endpoint = "db"
  }

  dynamic "application" {
    for_each = juju_application.postgresql
    content {
      offer_url = juju_offer.postgresql[0].url
    }
  }

  dynamic "application" {
    for_each = compact([var.postgresql_offer_url])
    content {
      offer_url = application.value
    }
  }
}

resource juju_integration "temporal_server_to_admin" {
  count = var.temporal_server_offer_url == null ? 1 : 0
  model = juju_model.temporal[0].name

  application {
    name = juju_application.temporal_server[0].name
    endpoint = "admin"
  }
  application {
    name = juju_application.temporal_admin[0].name
    endpoint = "admin"
  }
}


resource "juju_model" "temporal_worker" {
  name = "temporal-worker"
  cloud {
    name = var.juju_cloud_name
  }
  count = var.temporal_worker_offer_url == null ? 1 : 0
}

resource juju_application "temporal_worker" {
  name = "temporal-worker-k8s"
  count = var.temporal_worker_offer_url == null ? 1 : 0
  model = juju_model.temporal_worker[0].name
  units = 1
  charm {
    name = "temporal-worker-k8s"
    channel = var.temporal_worker_channel
    revision = var.temporal_worker_revision
  }
  resources = var.temporal_worker_resources
  config = {
    queue=var.temporal_task_queue
    namespace=var.temporal_namespace
  }
  lifecycle {
    ignore_changes = [
      config["host"],
    ]
  }
  provisioner "local-exec" {
    # This is needed until new temporal relations are implemented
    # Configure temporal server address for worker and msm.
    # Create namespace
    command = (<<-EOT
      juju wait-for application -m ${self.model} ${self.name} --timeout 3600s \
        --query='forEach(units, unit => unit.workload-status == "blocked" && unit.agent-status=="idle")'

      juju wait-for application -m ${juju_model.temporal[0].name} ${juju_application.temporal_server[0].name} --timeout 3600s \
        --query='forEach(units, unit => unit.workload-status == "active" && unit.agent-status=="idle")'


      TEMPORAL_IP=$(juju show-unit -m ${juju_model.temporal[0].name} temporal-k8s/0 | yq .temporal-k8s/0.address)
      juju config -m ${self.model} ${self.name} host=$TEMPORAL_IP:7233
      juju config -m ${juju_model.development.name} ${juju_application.msm.name} temporal-server-address=$TEMPORAL_IP:7233

      juju run -m ${juju_model.temporal[0].name} ${juju_application.temporal_admin[0].name}/leader tctl \
        args="--ns ${var.temporal_namespace} namespace register -rd 3" --wait 1m
    EOT
    )
  }
}
