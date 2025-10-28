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

# Raw Ideas Schema
resource "confluent_schema" "raw_ideas" {
  schema_registry_cluster {
    id = data.confluent_schema_registry_cluster.schema_registry.id
  }

  rest_endpoint = data.confluent_schema_registry_cluster.schema_registry.rest_endpoint

  subject_name = "${confluent_kafka_topic.agent_state_raw_ideas.topic_name}-value"
  format       = "AVRO"
  schema       = file("${path.module}/../agents/schemas/raw-ideas.avsc")

  credentials {
    key    = confluent_api_key.schema_registry_api_key.id
    secret = confluent_api_key.schema_registry_api_key.secret
  }
}

# Evaluation Layer Schemas (Phase 3 - Iron Triangle)

# Scope Challenge Schema
resource "confluent_schema" "scope_challenge" {
  schema_registry_cluster {
    id = data.confluent_schema_registry_cluster.schema_registry.id
  }

  rest_endpoint = data.confluent_schema_registry_cluster.schema_registry.rest_endpoint

  subject_name = "${confluent_kafka_topic.agent_state_scope_challenges.topic_name}-value"
  format       = "AVRO"
  schema       = file("${path.module}/../agents/schemas/scope-challenge.avsc")

  credentials {
    key    = confluent_api_key.schema_registry_api_key.id
    secret = confluent_api_key.schema_registry_api_key.secret
  }
}

# Time Challenge Schema
resource "confluent_schema" "time_challenge" {
  schema_registry_cluster {
    id = data.confluent_schema_registry_cluster.schema_registry.id
  }

  rest_endpoint = data.confluent_schema_registry_cluster.schema_registry.rest_endpoint

  subject_name = "${confluent_kafka_topic.agent_state_time_challenges.topic_name}-value"
  format       = "AVRO"
  schema       = file("${path.module}/../agents/schemas/time-challenge.avsc")

  credentials {
    key    = confluent_api_key.schema_registry_api_key.id
    secret = confluent_api_key.schema_registry_api_key.secret
  }
}

# Cost Challenge Schema
resource "confluent_schema" "cost_challenge" {
  schema_registry_cluster {
    id = data.confluent_schema_registry_cluster.schema_registry.id
  }

  rest_endpoint = data.confluent_schema_registry_cluster.schema_registry.rest_endpoint

  subject_name = "${confluent_kafka_topic.agent_state_cost_challenges.topic_name}-value"
  format       = "AVRO"
  schema       = file("${path.module}/../agents/schemas/cost-challenge.avsc")

  credentials {
    key    = confluent_api_key.schema_registry_api_key.id
    secret = confluent_api_key.schema_registry_api_key.secret
  }
}

# Decision Schema
resource "confluent_schema" "decision" {
  schema_registry_cluster {
    id = data.confluent_schema_registry_cluster.schema_registry.id
  }

  rest_endpoint = data.confluent_schema_registry_cluster.schema_registry.rest_endpoint

  subject_name = "${confluent_kafka_topic.agent_state_decisions.topic_name}-value"
  format       = "AVRO"
  schema       = file("${path.module}/../agents/schemas/decision.avsc")

  credentials {
    key    = confluent_api_key.schema_registry_api_key.id
    secret = confluent_api_key.schema_registry_api_key.secret
  }
}

# Outputs

output "agent_schema_ids" {
  description = "Schema Registry IDs for agent state schemas"
  value = {
    deployment       = confluent_schema.deployment_state.schema_identifier
    usage            = confluent_schema.usage_state.schema_identifier
    metrics          = confluent_schema.metrics_state.schema_identifier
    current          = confluent_schema.current_state.schema_identifier
    raw_ideas        = confluent_schema.raw_ideas.schema_identifier
    scope_challenge  = confluent_schema.scope_challenge.schema_identifier
    time_challenge   = confluent_schema.time_challenge.schema_identifier
    cost_challenge   = confluent_schema.cost_challenge.schema_identifier
    decision         = confluent_schema.decision.schema_identifier
  }
}
