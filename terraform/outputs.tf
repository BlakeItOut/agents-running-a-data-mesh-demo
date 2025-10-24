# Outputs for easy access to cluster details and agent integration

output "environment_id" {
  description = "The ID of the Confluent Cloud environment"
  value       = confluent_environment.data_mesh_env.id
}

output "environment_name" {
  description = "The name of the Confluent Cloud environment"
  value       = confluent_environment.data_mesh_env.display_name
}

output "kafka_cluster_id" {
  description = "The ID of the Kafka cluster"
  value       = confluent_kafka_cluster.datagen_cluster.id
}

output "kafka_cluster_name" {
  description = "The name of the Kafka cluster"
  value       = confluent_kafka_cluster.datagen_cluster.display_name
}

output "kafka_bootstrap_endpoint" {
  description = "The bootstrap endpoint for the Kafka cluster"
  value       = confluent_kafka_cluster.datagen_cluster.bootstrap_endpoint
}

output "kafka_rest_endpoint" {
  description = "The REST endpoint for the Kafka cluster"
  value       = confluent_kafka_cluster.datagen_cluster.rest_endpoint
}

output "schema_registry_id" {
  description = "The ID of the Schema Registry cluster"
  value       = data.confluent_schema_registry_cluster.schema_registry.id
}

output "schema_registry_rest_endpoint" {
  description = "The REST endpoint for Schema Registry"
  value       = data.confluent_schema_registry_cluster.schema_registry.rest_endpoint
}

output "schema_registry_api_key" {
  description = "The API key for Schema Registry"
  value       = confluent_api_key.schema_registry_api_key.id
  sensitive   = true
}

output "schema_registry_api_secret" {
  description = "The API secret for Schema Registry"
  value       = confluent_api_key.schema_registry_api_key.secret
  sensitive   = true
}

output "cluster_admin_api_key" {
  description = "The API key for cluster admin"
  value       = confluent_api_key.cluster_admin_api_key.id
  sensitive   = true
}

output "cluster_admin_api_secret" {
  description = "The API secret for cluster admin"
  value       = confluent_api_key.cluster_admin_api_key.secret
  sensitive   = true
}

output "topic_names" {
  description = "List of all created topic names"
  value       = [for topic in confluent_kafka_topic.datagen_topics : topic.topic_name]
}

output "connector_names" {
  description = "Map of template names to connector names"
  value = {
    for template, connector in confluent_connector.datagen_connectors :
    template => connector.config_nonsensitive["name"]
  }
}

output "connector_ids" {
  description = "Map of template names to connector IDs"
  value = {
    for template, connector in confluent_connector.datagen_connectors :
    template => connector.id
  }
}

output "service_account_ids" {
  description = "Map of template names to service account IDs"
  value = {
    for template, sa in confluent_service_account.connector_sa :
    template => sa.id
  }
}

output "quick_start_info" {
  description = "Quick start information for connecting to the cluster"
  value = {
    bootstrap_servers = confluent_kafka_cluster.datagen_cluster.bootstrap_endpoint
    schema_registry   = data.confluent_schema_registry_cluster.schema_registry.rest_endpoint
    environment_id    = confluent_environment.data_mesh_env.id
    cluster_id        = confluent_kafka_cluster.datagen_cluster.id
    total_topics      = length(confluent_kafka_topic.datagen_topics)
    total_connectors  = length(confluent_connector.datagen_connectors)
  }
}
