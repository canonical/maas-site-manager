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
    channel = "1.23/stable"
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
    channel = "1.23/stable"
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

resource juju_integration "temporal_server_to_admin_host_info" {
  count = var.temporal_server_offer_url == null ? 1 : 0
  model = juju_model.temporal[0].name

  application {
    name = juju_application.temporal_server[0].name
    endpoint = "temporal-host-info"
  }
  application {
    name = juju_application.temporal_admin[0].name
    endpoint = "temporal-host-info"
  }

  provisioner "local-exec" {
    # Create namespace
    command = (<<-EOT
      juju wait-for application -m ${juju_model.temporal[0].name} ${juju_application.temporal_server[0].name} --timeout 3600s \
        --query='forEach(units, unit => unit.workload-status == "active" && unit.agent-status=="idle")'

      juju run -m ${juju_model.temporal[0].name} ${juju_application.temporal_admin[0].name}/leader cli \
        args="operator namespace create --namespace ${var.temporal_namespace} --retention 3d" --wait 1m
    EOT
    )
  }
}



resource "juju_model" "temporal_worker" {
  name = "temporal-worker"
  cloud {
    name = var.juju_cloud_name
  }
}

resource juju_application "temporal_worker" {
  name = "temporal-worker-k8s"
  model = juju_model.temporal_worker.name
  units = 1
  charm {
    name = "temporal-worker-k8s"
    channel = "1.0/stable"
  }
  resources = var.temporal_worker_resources
  config = {
    queue=var.temporal_task_queue
    namespace=var.temporal_namespace
  }
}



resource "juju_offer" "temporal" {
  count = var.temporal_server_offer_url == null ? 1 : 0
  model            = juju_model.temporal[0].name
  application_name = juju_application.temporal_server[0].name
  endpoints         = ["temporal-host-info"]

}

resource "juju_offer" "temporal_worker" {
  model            = juju_model.temporal_worker.name
  application_name = juju_application.temporal_worker.name
  endpoints         = ["temporal-worker-info"]
}

resource "juju_integration" "temporal_to_temporal_worker" {
  model = juju_model.temporal_worker.name

  application {
    name = juju_application.temporal_worker.name
    endpoint = "temporal-host-info"
  }

  application {
    offer_url = var.temporal_server_offer_url == null ? juju_offer.temporal[0].url : var.temporal_server_offer_url
  }
}

resource "juju_integration" "temporal_to_msm" {
  model = juju_model.development.name

  application {
    name = juju_application.msm.name
    endpoint = "temporal-host-info"
  }

  application {
    offer_url = var.temporal_server_offer_url == null ? juju_offer.temporal[0].url : var.temporal_server_offer_url
  }
}

resource "juju_integration" "temporal_worker_to_msm" {
  model = juju_model.development.name

  application {
    name = juju_application.msm.name
    endpoint = "temporal-worker-info"
  }

  application {
    offer_url = juju_offer.temporal_worker.url
  }
}
