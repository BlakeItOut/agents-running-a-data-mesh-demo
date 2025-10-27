# Agent State Schemas
# Register Avro schemas for agent state topics in Schema Registry

# Deployment State Schema
resource "confluent_schema" "deployment_state" {
  schema_registry_cluster {
    id = data.confluent_schema_registry_cluster.schema_registry.id
  }

  rest_endpoint = data.confluent_schema_registry_cluster.schema_registry.rest_endpoint

  subject_name = "${confluent_kafka_topic.agent_state_deployment.topic_name}-value"
  format       = "AVRO"
  schema       = file("${path.module}/../agents/schemas/deployment-state.avsc")

  credentials {
    key    = confluent_api_key.schema_registry_api_key.id
    secret = confluent_api_key.schema_registry_api_key.secret
  }
}

# Usage State Schema
resource "confluent_schema" "usage_state" {
  schema_registry_cluster {
    id = data.confluent_schema_registry_cluster.schema_registry.id
  }

  rest_endpoint = data.confluent_schema_registry_cluster.schema_registry.rest_endpoint

  subject_name = "${confluent_kafka_topic.agent_state_usage.topic_name}-value"
  format       = "AVRO"
  schema       = file("${path.module}/../agents/schemas/usage-state.avsc")

  credentials {
    key    = confluent_api_key.schema_registry_api_key.id
    secret = confluent_api_key.schema_registry_api_key.secret
  }
}

# Metrics State Schema
resource "confluent_schema" "metrics_state" {
  schema_registry_cluster {
    id = data.confluent_schema_registry_cluster.schema_registry.id
  }

  rest_endpoint = data.confluent_schema_registry_cluster.schema_registry.rest_endpoint

  subject_name = "${confluent_kafka_topic.agent_state_metrics.topic_name}-value"
  format       = "AVRO"
  schema       = file("${path.module}/../agents/schemas/metrics-state.avsc")

  credentials {
    key    = confluent_api_key.schema_registry_api_key.id
    secret = confluent_api_key.schema_registry_api_key.secret
  }
}

# Current State Schema (aggregated)
resource "confluent_schema" "current_state" {
  schema_registry_cluster {
    id = data.confluent_schema_registry_cluster.schema_registry.id
  }

  rest_endpoint = data.confluent_schema_registry_cluster.schema_registry.rest_endpoint

  subject_name = "${confluent_kafka_topic.agent_state_current.topic_name}-value"
  format       = "AVRO"
  schema       = file("${path.module}/../agents/schemas/current-state.avsc")

  credentials {
    key    = confluent_api_key.schema_registry_api_key.id
    secret = confluent_api_key.schema_registry_api_key.secret
  }
}

# Outputs

output "agent_schema_ids" {
  description = "Schema Registry IDs for agent state schemas"
  value = {
    deployment = confluent_schema.deployment_state.schema_identifier
    usage      = confluent_schema.usage_state.schema_identifier
    metrics    = confluent_schema.metrics_state.schema_identifier
    current    = confluent_schema.current_state.schema_identifier
  }
}
