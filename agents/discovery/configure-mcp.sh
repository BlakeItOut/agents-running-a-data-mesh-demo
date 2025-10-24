#!/bin/bash
# Populate MCP config from Terraform outputs

cd ../../terraform

# Export all needed values
export ENVIRONMENT_ID=$(terraform output -raw environment_id)
export CLUSTER_ID=$(terraform output -raw kafka_cluster_id)
export KAFKA_ENDPOINT=$(terraform output -raw kafka_bootstrap_endpoint)
export SR_ENDPOINT=$(terraform output -raw schema_registry_rest_endpoint)
export SR_ID=$(terraform output -raw schema_registry_id)

# Get all agent credentials
export AGENT_CLOUD_KEY=$(terraform output -raw discovery_agent_cloud_api_key)
export AGENT_CLOUD_SECRET=$(terraform output -raw discovery_agent_cloud_api_secret)
export AGENT_CLUSTER_KEY=$(terraform output -raw discovery_agent_cluster_api_key)
export AGENT_CLUSTER_SECRET=$(terraform output -raw discovery_agent_cluster_api_secret)
export AGENT_SR_KEY=$(terraform output -raw discovery_agent_sr_api_key)
export AGENT_SR_SECRET=$(terraform output -raw discovery_agent_sr_api_secret)

# Strip SASL_SSL:// prefix from bootstrap endpoint for BOOTSTRAP_SERVERS
export BOOTSTRAP_ONLY=$(echo ${KAFKA_ENDPOINT} | sed 's|SASL_SSL://||')

# Extract REST endpoint from bootstrap endpoint (replace port 9092 with 443)
export KAFKA_REST_ENDPOINT=$(echo ${KAFKA_ENDPOINT} | sed 's|SASL_SSL://|https://|' | sed 's|:9092|:443|')

cd ../agents/discovery

# Create .env file for MCP server with correct variable names
cat > .env <<EOF
# Confluent Cloud API credentials (organization-level)
CONFLUENT_CLOUD_API_KEY=${AGENT_CLOUD_KEY}
CONFLUENT_CLOUD_API_SECRET=${AGENT_CLOUD_SECRET}
CONFLUENT_CLOUD_REST_ENDPOINT=https://api.confluent.cloud

# Kafka Cluster Configuration (cluster-specific)
KAFKA_ENV_ID=${ENVIRONMENT_ID}
KAFKA_CLUSTER_ID=${CLUSTER_ID}
BOOTSTRAP_SERVERS=${BOOTSTRAP_ONLY}
KAFKA_REST_ENDPOINT=${KAFKA_REST_ENDPOINT}
KAFKA_API_KEY=${AGENT_CLUSTER_KEY}
KAFKA_API_SECRET=${AGENT_CLUSTER_SECRET}

# Schema Registry Configuration
CONFLUENT_SCHEMA_REGISTRY_ID=${SR_ID}
SCHEMA_REGISTRY_ENDPOINT=${SR_ENDPOINT}
SCHEMA_REGISTRY_API_KEY=${AGENT_SR_KEY}
SCHEMA_REGISTRY_API_SECRET=${AGENT_SR_SECRET}
EOF

echo "MCP configuration complete! Credentials stored in .env"
echo ""
echo "Summary:"
echo "  - Cloud API Key: ${AGENT_CLOUD_KEY}"
echo "  - Cluster API Key: ${AGENT_CLUSTER_KEY}"
echo "  - Schema Registry API Key: ${AGENT_SR_KEY}"