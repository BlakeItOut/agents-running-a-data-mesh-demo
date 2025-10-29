# Real-Time Gaming Intelligence Platform Data Product
# Domain: gaming
# Owner: data-mesh-team
# Classification: INTERNAL

terraform {
  required_providers {
    confluent = {
      source  = "confluentinc/confluent"
      version = "~> 2.0"
    }
  }
}

# Reference existing infrastructure
data "confluent_kafka_cluster" "datagen_cluster" {
  id = var.cluster_id
  environment {
    id = var.environment_id
  }
}

data "confluent_environment" "datagen_env" {
  id = var.environment_id
}

data "confluent_schema_registry_cluster" "main" {
  id = var.schema_registry_cluster_id
  environment {
    id = var.environment_id
  }
}

# Reference admin API key for cluster operations
data "confluent_api_key" "cluster_admin" {
  id = var.cluster_admin_api_key_id
}

# Service Account for Data Product
resource "confluent_service_account" "gaming_intelligence_sa" {
  display_name = "gaming-intelligence-platform-sa"
  description  = "Service account for Real-Time Gaming Intelligence Platform data product"
}

# API Key for Service Account
resource "confluent_api_key" "gaming_intelligence_api_key" {
  display_name = "gaming-intelligence-platform-api-key"
  description  = "API key for Real-Time Gaming Intelligence Platform"
  owner {
    id          = confluent_service_account.gaming_intelligence_sa.id
    api_version = confluent_service_account.gaming_intelligence_sa.api_version
    kind        = confluent_service_account.gaming_intelligence_sa.kind
  }

  managed_resource {
    id          = data.confluent_kafka_cluster.datagen_cluster.id
    api_version = data.confluent_kafka_cluster.datagen_cluster.api_version
    kind        = data.confluent_kafka_cluster.datagen_cluster.kind

    environment {
      id = data.confluent_environment.datagen_env.id
    }
  }
}

# Output Topic
resource "confluent_kafka_topic" "gaming_intelligence_output" {
  kafka_cluster {
    id = data.confluent_kafka_cluster.datagen_cluster.id
  }

  topic_name       = "gaming.real-time-gaming-intelligence-platform"
  partitions_count = 6
  rest_endpoint    = data.confluent_kafka_cluster.datagen_cluster.rest_endpoint

  config = {
    "retention.ms"           = "604800000" # 7 days
    "cleanup.policy"         = "delete"
    "compression.type"       = "snappy"
    "min.insync.replicas"    = "2"
    "segment.ms"             = "3600000" # 1 hour
    "max.message.bytes"      = "1048576" # 1 MB
  }

  credentials {
    key    = data.confluent_api_key.cluster_admin.id
    secret = data.confluent_api_key.cluster_admin.secret
  }
}

# Schema Registry API Key for Service Account
resource "confluent_api_key" "gaming_intelligence_sr_api_key" {
  display_name = "gaming-intelligence-sr-api-key"
  description  = "Schema Registry API key for Real-Time Gaming Intelligence Platform"
  owner {
    id          = confluent_service_account.gaming_intelligence_sa.id
    api_version = confluent_service_account.gaming_intelligence_sa.api_version
    kind        = confluent_service_account.gaming_intelligence_sa.kind
  }

  managed_resource {
    id          = data.confluent_schema_registry_cluster.main.id
    api_version = data.confluent_schema_registry_cluster.main.api_version
    kind        = data.confluent_schema_registry_cluster.main.kind

    environment {
      id = data.confluent_environment.datagen_env.id
    }
  }
}

# Avro Schema for Output Topic
resource "confluent_schema" "gaming_intelligence_value_schema" {
  schema_registry_cluster {
    id = data.confluent_schema_registry_cluster.main.id
  }

  rest_endpoint = data.confluent_schema_registry_cluster.main.rest_endpoint

  subject_name = "${confluent_kafka_topic.gaming_intelligence_output.topic_name}-value"
  format       = "AVRO"
  schema = jsonencode({
    type = "record"
    name = "GamingIntelligence"
    namespace = "com.datamesh.gaming"
    doc = "Aggregated gaming intelligence combining player activity, game metadata, and player profiles"
    fields = [
      {
        name = "game_id"
        type = "string"
        doc = "Unique identifier for the game"
      },
      {
        name = "game_name"
        type = ["null", "string"]
        default = null
        doc = "Name of the game"
      },
      {
        name = "game_genre"
        type = ["null", "string"]
        default = null
        doc = "Genre of the game"
      },
      {
        name = "player_id"
        type = "string"
        doc = "Unique identifier for the player"
      },
      {
        name = "player_username"
        type = ["null", "string"]
        default = null
        doc = "Player username"
      },
      {
        name = "player_email"
        type = ["null", "string"]
        default = null
        doc = "Player email address"
      },
      {
        name = "player_level"
        type = ["null", "int"]
        default = null
        doc = "Current player level"
      },
      {
        name = "activity_type"
        type = "string"
        doc = "Type of player activity (e.g., login, achievement, purchase)"
      },
      {
        name = "session_id"
        type = ["null", "string"]
        default = null
        doc = "Session identifier"
      },
      {
        name = "score"
        type = ["null", "long"]
        default = null
        doc = "Score achieved in the activity"
      },
      {
        name = "duration_seconds"
        type = ["null", "int"]
        default = null
        doc = "Duration of activity in seconds"
      },
      {
        name = "total_sessions_1h"
        type = ["null", "long"]
        default = null
        doc = "Total sessions in the last hour (windowed aggregate)"
      },
      {
        name = "avg_score_1h"
        type = ["null", "double"]
        default = null
        doc = "Average score in the last hour (windowed aggregate)"
      },
      {
        name = "active_players_count"
        type = ["null", "long"]
        default = null
        doc = "Count of active players for this game"
      },
      {
        name = "event_timestamp"
        type = {
          type = "long"
          logicalType = "timestamp-millis"
        }
        doc = "Timestamp of the original activity event"
      },
      {
        name = "processing_timestamp"
        type = {
          type = "long"
          logicalType = "timestamp-millis"
        }
        doc = "Timestamp when this record was processed"
      }
    ]
  })

  credentials {
    key    = confluent_api_key.gaming_intelligence_sr_api_key.id
    secret = confluent_api_key.gaming_intelligence_sr_api_key.secret
  }
}

# RBAC: Grant read access to source topics
resource "confluent_role_binding" "gaming_intelligence_read_gaming_games" {
  principal   = "User:${confluent_service_account.gaming_intelligence_sa.id}"
  role_name   = "DeveloperRead"
  crn_pattern = "${data.confluent_kafka_cluster.datagen_cluster.rbac_crn}/kafka=${data.confluent_kafka_cluster.datagen_cluster.id}/topic=gaming_games"
}

resource "confluent_role_binding" "gaming_intelligence_read_gaming_players" {
  principal   = "User:${confluent_service_account.gaming_intelligence_sa.id}"
  role_name   = "DeveloperRead"
  crn_pattern = "${data.confluent_kafka_cluster.datagen_cluster.rbac_crn}/kafka=${data.confluent_kafka_cluster.datagen_cluster.id}/topic=gaming_players"
}

resource "confluent_role_binding" "gaming_intelligence_read_gaming_activity" {
  principal   = "User:${confluent_service_account.gaming_intelligence_sa.id}"
  role_name   = "DeveloperRead"
  crn_pattern = "${data.confluent_kafka_cluster.datagen_cluster.rbac_crn}/kafka=${data.confluent_kafka_cluster.datagen_cluster.id}/topic=gaming_player_activity"
}

# RBAC: Grant write access to output topic
resource "confluent_role_binding" "gaming_intelligence_write_output" {
  principal   = "User:${confluent_service_account.gaming_intelligence_sa.id}"
  role_name   = "DeveloperWrite"
  crn_pattern = "${data.confluent_kafka_cluster.datagen_cluster.rbac_crn}/kafka=${data.confluent_kafka_cluster.datagen_cluster.id}/topic=${confluent_kafka_topic.gaming_intelligence_output.topic_name}"
}

# RBAC: Grant access to consumer groups
resource "confluent_role_binding" "gaming_intelligence_consumer_group" {
  principal   = "User:${confluent_service_account.gaming_intelligence_sa.id}"
  role_name   = "DeveloperRead"
  crn_pattern = "${data.confluent_kafka_cluster.datagen_cluster.rbac_crn}/kafka=${data.confluent_kafka_cluster.datagen_cluster.id}/group=gaming-intelligence-*"
}

# RBAC: Grant Schema Registry access
resource "confluent_role_binding" "gaming_intelligence_sr_read" {
  principal   = "User:${confluent_service_account.gaming_intelligence_sa.id}"
  role_name   = "DeveloperRead"
  crn_pattern = "${data.confluent_schema_registry_cluster.main.resource_name}/subject=*"
}

resource "confluent_role_binding" "gaming_intelligence_sr_write" {
  principal   = "User:${confluent_service_account.gaming_intelligence_sa.id}"
  role_name   = "DeveloperWrite"
  crn_pattern = "${data.confluent_schema_registry_cluster.main.resource_name}/subject=${confluent_kafka_topic.gaming_intelligence_output.topic_name}-*"
}

# Variables
variable "cluster_id" {
  description = "The Kafka cluster ID"
  type        = string
}

variable "environment_id" {
  description = "The environment ID"
  type        = string
}

variable "schema_registry_cluster_id" {
  description = "The Schema Registry cluster ID"
  type        = string
}

variable "cluster_admin_api_key_id" {
  description = "The cluster admin API key ID"
  type        = string
}

# Outputs
output "gaming_intelligence_topic_name" {
  description = "Name of the gaming intelligence output topic"
  value       = confluent_kafka_topic.gaming_intelligence_output.topic_name
}

output "gaming_intelligence_service_account_id" {
  description = "Service account ID for gaming intelligence platform"
  value       = confluent_service_account.gaming_intelligence_sa.id
}

output "gaming_intelligence_api_key" {
  description = "API key for gaming intelligence platform (sensitive)"
  value       = confluent_api_key.gaming_intelligence_api_key.id
  sensitive   = true
}

output "gaming_intelligence_api_secret" {
  description = "API secret for gaming intelligence platform (sensitive)"
  value       = confluent_api_key.gaming_intelligence_api_key.secret
  sensitive   = true
}

output "gaming_intelligence_schema_id" {
  description = "Schema ID for gaming intelligence output"
  value       = confluent_schema.gaming_intelligence_value_schema.schema_identifier
}

output "gaming_intelligence_deployment_info" {
  description = "Quick reference for deployment"
  value = {
    domain              = "gaming"
    owner               = "data-mesh-team"
    classification      = "INTERNAL"
    output_topic        = confluent_kafka_topic.gaming_intelligence_output.topic_name
    partitions          = confluent_kafka_topic.gaming_intelligence_output.partitions_count
    retention_days      = 7
    source_topics       = ["gaming_games", "gaming_players", "gaming_player_activity"]
    processing_engine   = "ksqlDB"
    service_account     = confluent_service_account.gaming_intelligence_sa.display_name
  }
}
