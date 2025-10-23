# Service accounts for datagen connectors
# One service account per connector for granular access control

locals {
  # Create a map of template names to normalized service account names
  connector_service_accounts = {
    for template in var.connector_quickstart_templates :
    template => replace(template, "_", "-")
  }
}

resource "confluent_service_account" "connector_sa" {
  for_each = local.connector_service_accounts

  display_name = "sa-connector-${each.value}"
  description  = "Service account for ${each.key} datagen connector"
}

# Create API keys for connector service accounts
resource "confluent_api_key" "connector_api_key" {
  for_each = confluent_service_account.connector_sa

  display_name = "api-key-${each.key}"
  description  = "API Key for ${each.key} connector service account"

  owner {
    id          = each.value.id
    api_version = each.value.api_version
    kind        = each.value.kind
  }

  managed_resource {
    id          = confluent_kafka_cluster.datagen_cluster.id
    api_version = confluent_kafka_cluster.datagen_cluster.api_version
    kind        = confluent_kafka_cluster.datagen_cluster.kind

    environment {
      id = confluent_environment.data_mesh_env.id
    }
  }

  lifecycle {
    prevent_destroy = false
  }

  depends_on = [
    confluent_role_binding.connector_developer_write
  ]
}
