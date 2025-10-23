# Schema Registry Configuration
# Schema Registry is automatically enabled with Stream Governance in the environment
# We reference it as a data source after the environment is created

# Data source to get the Schema Registry cluster for this environment
data "confluent_schema_registry_cluster" "schema_registry" {
  environment {
    id = confluent_environment.data_mesh_env.id
  }

  depends_on = [
    confluent_environment.data_mesh_env
  ]
}

# Service account for Schema Registry
resource "confluent_service_account" "schema_registry_sa" {
  display_name = "schema-registry-sa"
  description  = "Service account for Schema Registry"
}

# Role binding for Schema Registry
resource "confluent_role_binding" "schema_registry_resource_owner" {
  principal   = "User:${confluent_service_account.schema_registry_sa.id}"
  role_name   = "ResourceOwner"
  crn_pattern = format("%s/%s", data.confluent_schema_registry_cluster.schema_registry.resource_name, "subject=*")

  lifecycle {
    prevent_destroy = false
  }
}

# API Key for Schema Registry
resource "confluent_api_key" "schema_registry_api_key" {
  display_name = "schema-registry-api-key"
  description  = "API Key for Schema Registry"

  owner {
    id          = confluent_service_account.schema_registry_sa.id
    api_version = confluent_service_account.schema_registry_sa.api_version
    kind        = confluent_service_account.schema_registry_sa.kind
  }

  managed_resource {
    id          = data.confluent_schema_registry_cluster.schema_registry.id
    api_version = data.confluent_schema_registry_cluster.schema_registry.api_version
    kind        = data.confluent_schema_registry_cluster.schema_registry.kind

    environment {
      id = confluent_environment.data_mesh_env.id
    }
  }

  lifecycle {
    prevent_destroy = false
  }

  depends_on = [
    confluent_role_binding.schema_registry_resource_owner
  ]
}
