# Kafka topics for all datagen templates
# One topic per connector/template

resource "confluent_kafka_topic" "datagen_topics" {
  for_each = toset(var.connector_quickstart_templates)

  kafka_cluster {
    id = confluent_kafka_cluster.datagen_cluster.id
  }

  topic_name       = each.key
  partitions_count = var.topic_partitions

  rest_endpoint = confluent_kafka_cluster.datagen_cluster.rest_endpoint

  config = var.topic_config

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
