variable "confluent_cloud_api_key" {
  description = "Confluent Cloud API Key (also set via CONFLUENT_CLOUD_API_KEY env var)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "confluent_cloud_api_secret" {
  description = "Confluent Cloud API Secret (also set via CONFLUENT_CLOUD_API_SECRET env var)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "environment_name" {
  description = "Name of the Confluent Cloud environment"
  type        = string
  default     = "data-mesh-demo"
}

variable "cluster_name" {
  description = "Name of the Kafka cluster"
  type        = string
  default     = "datagen-cluster"
}

variable "cloud_provider" {
  description = "Cloud provider for the cluster (AWS, GCP, or AZURE)"
  type        = string
  default     = "AWS"
}

variable "region" {
  description = "Cloud provider region"
  type        = string
  default     = "us-east-1"
}

variable "cluster_availability" {
  description = "Availability zone configuration (SINGLE_ZONE or MULTI_ZONE)"
  type        = string
  default     = "MULTI_ZONE"
}

variable "connector_tasks_max" {
  description = "Maximum number of tasks for each datagen connector"
  type        = number
  default     = 1
}

variable "connector_kafka_max_interval" {
  description = "Maximum interval in ms between messages for datagen connectors"
  type        = number
  default     = 1000
}

variable "connector_quickstart_templates" {
  description = "List of all datagen quickstart templates to deploy"
  type        = list(string)
  default = [
    "campaign_finance",
    "clickstream_codes",
    "clickstream",
    "clickstream_users",
    "credit_cards",
    "device_information",
    "fleet_mgmt_description",
    "fleet_mgmt_location",
    "fleet_mgmt_sensors",
    "gaming_games",
    "gaming_player_activity",
    "gaming_players",
    "insurance_customer_activity",
    "insurance_customers",
    "insurance_offers",
    "inventory",
    "orders",
    "pageviews",
    "payroll_bonus",
    "payroll_employee",
    "payroll_employee_location",
    "pizza_orders",
    "pizza_orders_cancelled",
    "pizza_orders_completed",
    "product",
    "purchases",
    "ratings",
    "shoe_clickstream",
    "shoe_customers",
    "shoe_orders",
    "shoes",
    "siem_logs",
    "stock_trades",
    "stores",
    "syslog_logs",
    "transactions",
    "users"
  ]
}

variable "topic_partitions" {
  description = "Default number of partitions for each topic"
  type        = number
  default     = 6
}

variable "topic_config" {
  description = "Default topic configuration"
  type        = map(string)
  default = {
    "retention.ms"    = "604800000" # 7 days
    "segment.ms"      = "86400000"  # 1 day
    "cleanup.policy"  = "delete"
  }
}
