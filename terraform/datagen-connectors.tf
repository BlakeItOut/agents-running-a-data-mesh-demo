# Datagen Source Connectors
# One connector per quickstart template, each writing to its corresponding topic

locals {
  # Map template names to their quickstart values
  # Most templates use uppercase versions, but we'll normalize them
  template_quickstart_map = {
    campaign_finance              = "CAMPAIGN_FINANCE"
    clickstream_codes             = "CLICKSTREAM_CODES"
    clickstream                   = "CLICKSTREAM"
    clickstream_users             = "CLICKSTREAM_USERS"
    credit_cards                  = "CREDIT_CARDS"
    device_information            = "DEVICE_INFORMATION"
    fleet_mgmt_description        = "FLEET_MGMT_DESCRIPTION"
    fleet_mgmt_location           = "FLEET_MGMT_LOCATION"
    fleet_mgmt_sensors            = "FLEET_MGMT_SENSORS"
    gaming_games                  = "GAMING_GAMES"
    gaming_player_activity        = "GAMING_PLAYER_ACTIVITY"
    gaming_players                = "GAMING_PLAYERS"
    insurance_customer_activity   = "INSURANCE_CUSTOMER_ACTIVITY"
    insurance_customers           = "INSURANCE_CUSTOMERS"
    insurance_offers              = "INSURANCE_OFFERS"
    inventory                     = "INVENTORY"
    orders                        = "ORDERS"
    pageviews                     = "PAGEVIEWS"
    payroll_bonus                 = "PAYROLL_BONUS"
    payroll_employee              = "PAYROLL_EMPLOYEE"
    payroll_employee_location     = "PAYROLL_EMPLOYEE_LOCATION"
    pizza_orders                  = "PIZZA_ORDERS"
    pizza_orders_cancelled        = "PIZZA_ORDERS_CANCELLED"
    pizza_orders_completed        = "PIZZA_ORDERS_COMPLETED"
    product                       = "PRODUCT"
    purchase                      = "PURCHASE"
    ratings                       = "RATINGS"
    shoe_clickstream              = "SHOE_CLICKSTREAM"
    shoe_customers                = "SHOE_CUSTOMERS"
    shoe_orders                   = "SHOE_ORDERS"
    shoes                         = "SHOES"
    siem_logs                     = "SIEM_LOGS"
    stock_trades                  = "STOCK_TRADES"
    stores                        = "STORES"
    syslog_logs                   = "SYSLOG_LOGS"
    transactions                  = "TRANSACTIONS"
    users_array_map               = "USERS_ARRAY_MAP"
    users                         = "USERS"
  }
}

resource "confluent_connector" "datagen_connectors" {
  for_each = toset(var.connector_quickstart_templates)

  environment {
    id = confluent_environment.data_mesh_env.id
  }

  kafka_cluster {
    id = confluent_kafka_cluster.datagen_cluster.id
  }

  config_sensitive = {
    "kafka.api.key"    = confluent_api_key.connector_api_key[each.key].id
    "kafka.api.secret" = confluent_api_key.connector_api_key[each.key].secret
  }

  config_nonsensitive = {
    "connector.class"          = "DatagenSource"
    "name"                     = "datagen-${each.key}"
    "kafka.auth.mode"          = "SERVICE_ACCOUNT"
    "kafka.service.account.id" = confluent_service_account.connector_sa[each.key].id
    "kafka.topic"              = confluent_kafka_topic.datagen_topics[each.key].topic_name
    "output.data.format"       = "AVRO"
    "quickstart"               = local.template_quickstart_map[each.key]
    "tasks.max"                = tostring(var.connector_tasks_max)
    "max.interval"             = tostring(var.connector_kafka_max_interval)
  }

  lifecycle {
    prevent_destroy = false
  }

  depends_on = [
    confluent_kafka_topic.datagen_topics,
    confluent_role_binding.connector_developer_write,
    confluent_role_binding.connector_developer_read_cluster,
    confluent_api_key.connector_api_key
  ]
}
