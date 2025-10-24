# Discovery Agent Service Account
resource "confluent_service_account" "discovery_agent" {
  display_name = "discovery-agent"
  description  = "Service account for Discovery Agent to inventory topics and connectors"
}

# Cloud API Key for Discovery Agent (organization-level access)
resource "confluent_api_key" "discovery_agent_cloud_key" {
  display_name = "discovery-agent-cloud-api-key"
  description  = "Cloud API Key for Discovery Agent to list environments, clusters, etc."

  owner {
    id          = confluent_service_account.discovery_agent.id
    api_version = confluent_service_account.discovery_agent.api_version
    kind        = confluent_service_account.discovery_agent.kind
  }

  lifecycle {
    prevent_destroy = false
  }
}

# API Key for Discovery Agent (cluster access)
resource "confluent_api_key" "discovery_agent_cluster_key" {
  display_name = "discovery-agent-cluster-api-key"
  description  = "Cluster API Key for Discovery Agent"

  owner {
    id          = confluent_service_account.discovery_agent.id
    api_version = confluent_service_account.discovery_agent.api_version
    kind        = confluent_service_account.discovery_agent.kind
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
}

# API Key for Discovery Agent (Schema Registry access)
resource "confluent_api_key" "discovery_agent_sr_key" {
  display_name = "discovery-agent-sr-api-key"
  description  = "Schema Registry API Key for Discovery Agent"

  owner {
    id          = confluent_service_account.discovery_agent.id
    api_version = confluent_service_account.discovery_agent.api_version
    kind        = confluent_service_account.discovery_agent.kind
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
}

# RBAC: Grant DeveloperRead on all topics
resource "confluent_role_binding" "discovery_agent_read_topics" {
  principal   = "User:${confluent_service_account.discovery_agent.id}"
  role_name   = "DeveloperRead"
  crn_pattern = "${confluent_kafka_cluster.datagen_cluster.rbac_crn}/kafka=${confluent_kafka_cluster.datagen_cluster.id}/topic=*"

  lifecycle {
    prevent_destroy = false
  }
}

# RBAC: Grant CloudClusterAdmin for connector/cluster metadata access
# Note: Could use more restrictive role, but CloudClusterAdmin ensures full read access
resource "confluent_role_binding" "discovery_agent_cluster_admin" {
  principal   = "User:${confluent_service_account.discovery_agent.id}"
  role_name   = "CloudClusterAdmin"
  crn_pattern = confluent_kafka_cluster.datagen_cluster.rbac_crn

  lifecycle {
    prevent_destroy = false
  }
}

# RBAC: Grant EnvironmentAdmin for listing clusters and connectors in environment
resource "confluent_role_binding" "discovery_agent_env_admin" {
  principal   = "User:${confluent_service_account.discovery_agent.id}"
  role_name   = "EnvironmentAdmin"
  crn_pattern = confluent_environment.data_mesh_env.resource_name

  lifecycle {
    prevent_destroy = false
  }
}

# Output agent credentials for MCP configuration
output "discovery_agent_cloud_api_key" {
  description = "Discovery Agent Cloud API key (organization-level)"
  value       = confluent_api_key.discovery_agent_cloud_key.id
  sensitive   = true
}

output "discovery_agent_cloud_api_secret" {
  description = "Discovery Agent Cloud API secret (organization-level)"
  value       = confluent_api_key.discovery_agent_cloud_key.secret
  sensitive   = true
}

output "discovery_agent_cluster_api_key" {
  description = "Discovery Agent cluster API key"
  value       = confluent_api_key.discovery_agent_cluster_key.id
  sensitive   = true
}

output "discovery_agent_cluster_api_secret" {
  description = "Discovery Agent cluster API secret"
  value       = confluent_api_key.discovery_agent_cluster_key.secret
  sensitive   = true
}

output "discovery_agent_sr_api_key" {
  description = "Discovery Agent Schema Registry API key"
  value       = confluent_api_key.discovery_agent_sr_key.id
  sensitive   = true
}

output "discovery_agent_sr_api_secret" {
  description = "Discovery Agent Schema Registry API secret"
  value       = confluent_api_key.discovery_agent_sr_key.secret
  sensitive   = true
}