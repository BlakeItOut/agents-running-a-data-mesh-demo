# Agent State Topics
# These topics use log compaction to maintain only the latest state per key
# All topics have short names for easier consumption

# Pre-Current-State Topics (Input to Current State)

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
    key    = confluent_api_key.cluster_admin_api_key.id
    secret = confluent_api_key.cluster_admin_api_key.secret
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
    key    = confluent_api_key.cluster_admin_api_key.id
    secret = confluent_api_key.cluster_admin_api_key.secret
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
    key    = confluent_api_key.cluster_admin_api_key.id
    secret = confluent_api_key.cluster_admin_api_key.secret
  }
}

# Aggregated Current State Topic (Output from Current State)

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
    key    = confluent_api_key.cluster_admin_api_key.id
    secret = confluent_api_key.cluster_admin_api_key.secret
  }
}

# Raw Ideas Topic (Output from Learning Agent)

resource "confluent_kafka_topic" "agent_state_raw_ideas" {
  kafka_cluster {
    id = confluent_kafka_cluster.datagen_cluster.id
  }

  rest_endpoint = confluent_kafka_cluster.datagen_cluster.rest_endpoint

  topic_name    = "agent-state-raw-ideas"
  partitions_count = 1

  config = {
    "cleanup.policy"      = "compact"
    "compression.type"    = "snappy"
    "retention.ms"        = "-1"
    "min.compaction.lag.ms" = "60000"
  }

  credentials {
    key    = confluent_api_key.cluster_admin_api_key.id
    secret = confluent_api_key.cluster_admin_api_key.secret
  }
}

# Evaluation Layer Topics (Phase 3 - Iron Triangle)

resource "confluent_kafka_topic" "agent_state_scope_challenges" {
  kafka_cluster {
    id = confluent_kafka_cluster.datagen_cluster.id
  }

  rest_endpoint = confluent_kafka_cluster.datagen_cluster.rest_endpoint

  topic_name    = "agent-state-scope-challenges"
  partitions_count = 1

  config = {
    "cleanup.policy"      = "compact"
    "compression.type"    = "snappy"
    "retention.ms"        = "-1"
    "min.compaction.lag.ms" = "60000"
  }

  credentials {
    key    = confluent_api_key.cluster_admin_api_key.id
    secret = confluent_api_key.cluster_admin_api_key.secret
  }
}

resource "confluent_kafka_topic" "agent_state_time_challenges" {
  kafka_cluster {
    id = confluent_kafka_cluster.datagen_cluster.id
  }

  rest_endpoint = confluent_kafka_cluster.datagen_cluster.rest_endpoint

  topic_name    = "agent-state-time-challenges"
  partitions_count = 1

  config = {
    "cleanup.policy"      = "compact"
    "compression.type"    = "snappy"
    "retention.ms"        = "-1"
    "min.compaction.lag.ms" = "60000"
  }

  credentials {
    key    = confluent_api_key.cluster_admin_api_key.id
    secret = confluent_api_key.cluster_admin_api_key.secret
  }
}

resource "confluent_kafka_topic" "agent_state_cost_challenges" {
  kafka_cluster {
    id = confluent_kafka_cluster.datagen_cluster.id
  }

  rest_endpoint = confluent_kafka_cluster.datagen_cluster.rest_endpoint

  topic_name    = "agent-state-cost-challenges"
  partitions_count = 1

  config = {
    "cleanup.policy"      = "compact"
    "compression.type"    = "snappy"
    "retention.ms"        = "-1"
    "min.compaction.lag.ms" = "60000"
  }

  credentials {
    key    = confluent_api_key.cluster_admin_api_key.id
    secret = confluent_api_key.cluster_admin_api_key.secret
  }
}

resource "confluent_kafka_topic" "agent_state_decisions" {
  kafka_cluster {
    id = confluent_kafka_cluster.datagen_cluster.id
  }

  rest_endpoint = confluent_kafka_cluster.datagen_cluster.rest_endpoint

  topic_name    = "agent-state-decisions"
  partitions_count = 1

  config = {
    "cleanup.policy"      = "compact"
    "compression.type"    = "snappy"
    "retention.ms"        = "-1"
    "min.compaction.lag.ms" = "60000"
  }

  credentials {
    key    = confluent_api_key.cluster_admin_api_key.id
    secret = confluent_api_key.cluster_admin_api_key.secret
  }
}

# Outputs for agent configuration

output "agent_topic_names" {
  description = "Names of all agent state topics"
  value = {
    deployment        = confluent_kafka_topic.agent_state_deployment.topic_name
    usage             = confluent_kafka_topic.agent_state_usage.topic_name
    metrics           = confluent_kafka_topic.agent_state_metrics.topic_name
    current           = confluent_kafka_topic.agent_state_current.topic_name
    raw_ideas         = confluent_kafka_topic.agent_state_raw_ideas.topic_name
    scope_challenges  = confluent_kafka_topic.agent_state_scope_challenges.topic_name
    time_challenges   = confluent_kafka_topic.agent_state_time_challenges.topic_name
    cost_challenges   = confluent_kafka_topic.agent_state_cost_challenges.topic_name
    decisions         = confluent_kafka_topic.agent_state_decisions.topic_name
  }
}
