# Real-Time Gaming Intelligence Platform Data Product
# Domain: gaming
# Owner: data-mesh-team
# Classification: INTERNAL
#
# This data product aggregates real-time gaming data from three source topics:
# - gaming_games: Game catalog and metadata
# - gaming_players: Player profiles and account information
# - gaming_player_activity: Real-time player actions and events
#
# The aggregated data enables real-time gaming analytics, player behavior tracking,
# and game performance monitoring.

# ============================================================================
# Topic Configuration
# ============================================================================

resource "confluent_kafka_topic" "gaming_intelligence_platform" {
  kafka_cluster {
    id = confluent_kafka_cluster.datagen_cluster.id
  }

  rest_endpoint = confluent_kafka_cluster.datagen_cluster.rest_endpoint

  topic_name       = "gaming.real-time-gaming-intelligence-platform"
  partitions_count = 6

  config = {
    "cleanup.policy" = "delete"
    "retention.ms"   = "604800000"  # 7 days
    "compression.type" = "snappy"
    "min.insync.replicas" = "2"
  }

  credentials {
    key    = confluent_api_key.cluster_admin_api_key.id
    secret = confluent_api_key.cluster_admin_api_key.secret
  }

  lifecycle {
    prevent_destroy = false
  }

  depends_on = [
    confluent_role_binding.cluster_admin_binding
  ]
}

# ============================================================================
# Service Account for Data Product Access
# ============================================================================

resource "confluent_service_account" "gaming_intelligence_sa" {
  display_name = "gaming-intelligence-sa"
  description  = "Service account for Real-Time Gaming Intelligence Platform data product"
}

# Grant read access to source topics
resource "confluent_kafka_acl" "gaming_intelligence_read_games" {
  kafka_cluster {
    id = confluent_kafka_cluster.datagen_cluster.id
  }
  rest_endpoint = confluent_kafka_cluster.datagen_cluster.rest_endpoint

  resource_type = "TOPIC"
  resource_name = "gaming_games"
  pattern_type  = "LITERAL"
  principal     = "User:${confluent_service_account.gaming_intelligence_sa.id}"
  operation     = "READ"
  permission    = "ALLOW"
  host          = "*"

  credentials {
    key    = confluent_api_key.cluster_admin_api_key.id
    secret = confluent_api_key.cluster_admin_api_key.secret
  }
}

resource "confluent_kafka_acl" "gaming_intelligence_read_players" {
  kafka_cluster {
    id = confluent_kafka_cluster.datagen_cluster.id
  }
  rest_endpoint = confluent_kafka_cluster.datagen_cluster.rest_endpoint

  resource_type = "TOPIC"
  resource_name = "gaming_players"
  pattern_type  = "LITERAL"
  principal     = "User:${confluent_service_account.gaming_intelligence_sa.id}"
  operation     = "READ"
  permission    = "ALLOW"
  host          = "*"

  credentials {
    key    = confluent_api_key.cluster_admin_api_key.id
    secret = confluent_api_key.cluster_admin_api_key.secret
  }
}

resource "confluent_kafka_acl" "gaming_intelligence_read_activity" {
  kafka_cluster {
    id = confluent_kafka_cluster.datagen_cluster.id
  }
  rest_endpoint = confluent_kafka_cluster.datagen_cluster.rest_endpoint

  resource_type = "TOPIC"
  resource_name = "gaming_player_activity"
  pattern_type  = "LITERAL"
  principal     = "User:${confluent_service_account.gaming_intelligence_sa.id}"
  operation     = "READ"
  permission    = "ALLOW"
  host          = "*"

  credentials {
    key    = confluent_api_key.cluster_admin_api_key.id
    secret = confluent_api_key.cluster_admin_api_key.secret
  }
}

# Grant read access to consumer group for source topics
resource "confluent_kafka_acl" "gaming_intelligence_consumer_group" {
  kafka_cluster {
    id = confluent_kafka_cluster.datagen_cluster.id
  }
  rest_endpoint = confluent_kafka_cluster.datagen_cluster.rest_endpoint

  resource_type = "GROUP"
  resource_name = "gaming-intelligence-"
  pattern_type  = "PREFIXED"
  principal     = "User:${confluent_service_account.gaming_intelligence_sa.id}"
  operation     = "READ"
  permission    = "ALLOW"
  host          = "*"

  credentials {
    key    = confluent_api_key.cluster_admin_api_key.id
    secret = confluent_api_key.cluster_admin_api_key.secret
  }
}

# Grant write access to data product topic
resource "confluent_kafka_acl" "gaming_intelligence_write" {
  kafka_cluster {
    id = confluent_kafka_cluster.datagen_cluster.id
  }
  rest_endpoint = confluent_kafka_cluster.datagen_cluster.rest_endpoint

  resource_type = "TOPIC"
  resource_name = "gaming.real-time-gaming-intelligence-platform"
  pattern_type  = "LITERAL"
  principal     = "User:${confluent_service_account.gaming_intelligence_sa.id}"
  operation     = "WRITE"
  permission    = "ALLOW"
  host          = "*"

  credentials {
    key    = confluent_api_key.cluster_admin_api_key.id
    secret = confluent_api_key.cluster_admin_api_key.secret
  }
}

# Grant read access for consumers of the data product
resource "confluent_kafka_acl" "gaming_intelligence_read_product" {
  kafka_cluster {
    id = confluent_kafka_cluster.datagen_cluster.id
  }
  rest_endpoint = confluent_kafka_cluster.datagen_cluster.rest_endpoint

  resource_type = "TOPIC"
  resource_name = "gaming.real-time-gaming-intelligence-platform"
  pattern_type  = "LITERAL"
  principal     = "User:${confluent_service_account.gaming_intelligence_sa.id}"
  operation     = "READ"
  permission    = "ALLOW"
  host          = "*"

  credentials {
    key    = confluent_api_key.cluster_admin_api_key.id
    secret = confluent_api_key.cluster_admin_api_key.secret
  }
}

# ============================================================================
# API Key for Data Product Service Account
# ============================================================================

resource "confluent_api_key" "gaming_intelligence_api_key" {
  display_name = "gaming-intelligence-api-key"
  description  = "API Key for Gaming Intelligence Platform data product"

  owner {
    id          = confluent_service_account.gaming_intelligence_sa.id
    api_version = confluent_service_account.gaming_intelligence_sa.api_version
    kind        = confluent_service_account.gaming_intelligence_sa.kind
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
    confluent_kafka_acl.gaming_intelligence_read_games,
    confluent_kafka_acl.gaming_intelligence_read_players,
    confluent_kafka_acl.gaming_intelligence_read_activity,
    confluent_kafka_acl.gaming_intelligence_write,
    confluent_kafka_acl.gaming_intelligence_read_product,
    confluent_kafka_acl.gaming_intelligence_consumer_group
  ]
}

# ============================================================================
# Outputs
# ============================================================================

output "gaming_intelligence_platform_topic" {
  description = "Name of the Gaming Intelligence Platform data product topic"
  value       = confluent_kafka_topic.gaming_intelligence_platform.topic_name
}

output "gaming_intelligence_platform_service_account_id" {
  description = "Service account ID for Gaming Intelligence Platform"
  value       = confluent_service_account.gaming_intelligence_sa.id
}

output "gaming_intelligence_platform_api_key" {
  description = "API key for Gaming Intelligence Platform service account"
  value       = confluent_api_key.gaming_intelligence_api_key.id
  sensitive   = true
}

output "gaming_intelligence_platform_api_secret" {
  description = "API secret for Gaming Intelligence Platform service account"
  value       = confluent_api_key.gaming_intelligence_api_key.secret
  sensitive   = true
}

output "gaming_intelligence_platform_info" {
  description = "Quick reference information for Gaming Intelligence Platform"
  value = {
    topic_name        = confluent_kafka_topic.gaming_intelligence_platform.topic_name
    partitions        = confluent_kafka_topic.gaming_intelligence_platform.partitions_count
    retention_ms      = confluent_kafka_topic.gaming_intelligence_platform.config["retention.ms"]
    domain            = "gaming"
    classification    = "INTERNAL"
    owner             = "data-mesh-team"
    source_topics     = ["gaming_games", "gaming_players", "gaming_player_activity"]
    processing_engine = "ksqlDB"
  }
}
