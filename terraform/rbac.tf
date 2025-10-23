# RBAC Role Bindings for Connector Service Accounts
# Grant DeveloperWrite role for each connector service account

resource "confluent_role_binding" "connector_developer_write" {
  for_each = confluent_service_account.connector_sa

  principal   = "User:${each.value.id}"
  role_name   = "DeveloperWrite"
  crn_pattern = "${confluent_kafka_cluster.datagen_cluster.rbac_crn}/kafka=${confluent_kafka_cluster.datagen_cluster.id}/topic=*"

  lifecycle {
    prevent_destroy = false
  }
}

# Grant DeveloperRead role on the cluster for monitoring
resource "confluent_role_binding" "connector_developer_read_cluster" {
  for_each = confluent_service_account.connector_sa

  principal   = "User:${each.value.id}"
  role_name   = "DeveloperRead"
  crn_pattern = confluent_kafka_cluster.datagen_cluster.rbac_crn

  lifecycle {
    prevent_destroy = false
  }
}
