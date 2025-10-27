# Agent State Topics
# These topics use log compaction to maintain only the latest state per key
# All topics have short names for easier consumption

# Pre-Current-State Topics (Input to Current State Prompt)

resource "confluent_kafka_topic" "agent_state_deployment" {
  kafka_cluster {
    id = confluent_kafka_cluster.datagen_cluster.id
  }

  rest_endpoint = confluent_kafka_cluster.datagen_cluster.rest_endpoint

  topic_name    = "agent-state-deployment"
  partitions_count = 1  # Single partition for total ordering

  config = {
    "cleanup.policy"      = "compact"
    "compression.type"    = "snappy"
    "retention.ms"        = "-1"  # Infinite retention
    "min.compaction.lag.ms" = "60000"  # Wait 1 minute before compacting
  }

  credentials {
    key    = confluent_api_key.cluster_admin_key.id
    secret = confluent_api_key.cluster_admin_key.secret
  }
}

resource "confluent_kafka_topic" "agent_state_usage" {
  kafka_cluster {
    id = confluent_kafka_cluster.datagen_cluster.id
  }

  rest_endpoint = confluent_kafka_cluster.datagen_cluster.rest_endpoint

  topic_name    = "agent-state-usage"
  partitions_count = 1

  config = {
    "cleanup.policy"      = "compact"
    "compression.type"    = "snappy"
    "retention.ms"        = "-1"
    "min.compaction.lag.ms" = "60000"
  }

  credentials {
    key    = confluent_api_key.cluster_admin_key.id
    secret = confluent_api_key.cluster_admin_key.secret
  }
}

resource "confluent_kafka_topic" "agent_state_metrics" {
  kafka_cluster {
    id = confluent_kafka_cluster.datagen_cluster.id
  }

  rest_endpoint = confluent_kafka_cluster.datagen_cluster.rest_endpoint

  topic_name    = "agent-state-metrics"
  partitions_count = 1

  config = {
    "cleanup.policy"      = "compact"
    "compression.type"    = "snappy"
    "retention.ms"        = "-1"
    "min.compaction.lag.ms" = "60000"
  }

  credentials {
    key    = confluent_api_key.cluster_admin_key.id
    secret = confluent_api_key.cluster_admin_key.secret
  }
}

# Aggregated Current State Topic (Output from Current State Prompt)

resource "confluent_kafka_topic" "agent_state_current" {
  kafka_cluster {
    id = confluent_kafka_cluster.datagen_cluster.id
  }

  rest_endpoint = confluent_kafka_cluster.datagen_cluster.rest_endpoint

  topic_name    = "agent-state-current"
  partitions_count = 1

  config = {
    "cleanup.policy"      = "compact"
    "compression.type"    = "snappy"
    "retention.ms"        = "-1"
    "min.compaction.lag.ms" = "60000"
  }

  credentials {
    key    = confluent_api_key.cluster_admin_key.id
    secret = confluent_api_key.cluster_admin_key.secret
  }
}

# Outputs for agent configuration

output "agent_topic_names" {
  description = "Names of all agent state topics"
  value = {
    deployment = confluent_kafka_topic.agent_state_deployment.topic_name
    usage      = confluent_kafka_topic.agent_state_usage.topic_name
    metrics    = confluent_kafka_topic.agent_state_metrics.topic_name
    current    = confluent_kafka_topic.agent_state_current.topic_name
  }
}
