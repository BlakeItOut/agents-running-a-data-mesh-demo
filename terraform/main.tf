terraform {
  required_version = ">= 1.0"

  required_providers {
    confluent = {
      source  = "confluentinc/confluent"
      version = "~> 2.0"
    }
  }
}

provider "confluent" {
  cloud_api_key    = var.confluent_cloud_api_key != "" ? var.confluent_cloud_api_key : null
  cloud_api_secret = var.confluent_cloud_api_secret != "" ? var.confluent_cloud_api_secret : null
}

# Create Confluent Cloud Environment
resource "confluent_environment" "data_mesh_env" {
  display_name = var.environment_name

  lifecycle {
    prevent_destroy = false
  }
}

# Create Standard Kafka Cluster with RBAC support
resource "confluent_kafka_cluster" "datagen_cluster" {
  display_name = var.cluster_name
  availability = var.cluster_availability
  cloud        = var.cloud_provider
  region       = var.region

  standard {}

  environment {
    id = confluent_environment.data_mesh_env.id
  }

  lifecycle {
    prevent_destroy = false
  }
}

# Create cluster admin service account
resource "confluent_service_account" "cluster_admin" {
  display_name = "${var.cluster_name}-admin"
  description  = "Service account for cluster administration"
}

# Create API key for cluster admin
resource "confluent_api_key" "cluster_admin_api_key" {
  display_name = "${var.cluster_name}-admin-api-key"
  description  = "API Key for cluster admin service account"

  owner {
    id          = confluent_service_account.cluster_admin.id
    api_version = confluent_service_account.cluster_admin.api_version
    kind        = confluent_service_account.cluster_admin.kind
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
}

# Grant CloudClusterAdmin role to admin service account
resource "confluent_role_binding" "cluster_admin_binding" {
  principal   = "User:${confluent_service_account.cluster_admin.id}"
  role_name   = "CloudClusterAdmin"
  crn_pattern = confluent_kafka_cluster.datagen_cluster.rbac_crn
}
