# Confluent Cloud Data Mesh Demo - Terraform Setup

This Terraform configuration spins up a complete Confluent Cloud environment with all 38 datagen connector templates, creating a realistic "raw data mess" for autonomous agents to organize into a data mesh.

## Overview

This setup creates:

- **1 Confluent Cloud Environment** (`data-mesh-demo`)
- **1 Standard Kafka Cluster** (multi-zone, RBAC-enabled)
- **38 Kafka Topics** (one per datagen template)
- **Schema Registry** with Avro schemas for all topics
- **38 Datagen Connectors** generating continuous sample data
- **39 Service Accounts** (1 admin + 38 connector-specific)
- **RBAC Role Bindings** (DeveloperWrite/DeveloperRead roles)

### Datagen Templates Included

The setup includes all available Confluent datagen quickstart templates across multiple domains:

**Financial/Trading (4):** campaign_finance, credit_cards, stock_trades, transactions

**E-commerce/Retail (10):** inventory, orders, product, purchase, shoes, shoe_clickstream, shoe_customers, shoe_orders, stores, ratings

**Pizza Delivery (3):** pizza_orders, pizza_orders_cancelled, pizza_orders_completed

**Web Analytics (4):** clickstream, clickstream_codes, clickstream_users, pageviews

**Users (2):** users, users_array_map

**Gaming (3):** gaming_games, gaming_players, gaming_player_activity

**Insurance (3):** insurance_customers, insurance_offers, insurance_customer_activity

**Fleet Management (3):** fleet_mgmt_location, fleet_mgmt_sensors, fleet_mgmt_description

**HR/Payroll (3):** payroll_employee, payroll_employee_location, payroll_bonus

**Security/Logging (2):** siem_logs, syslog_logs

**IoT (1):** device_information

## Prerequisites

1. **Confluent Cloud Account**
   - Sign up at https://confluent.cloud
   - Create Cloud API credentials (not cluster-specific)

2. **Terraform**
   - Install Terraform >= 1.0
   - https://www.terraform.io/downloads

3. **Environment Variables**
   ```bash
   export CONFLUENT_CLOUD_API_KEY="<your-api-key>"
   export CONFLUENT_CLOUD_API_SECRET="<your-api-secret>"
   ```

## Quick Start

### 1. Set Confluent Cloud Credentials

```bash
export CONFLUENT_CLOUD_API_KEY="your-cloud-api-key"
export CONFLUENT_CLOUD_API_SECRET="your-cloud-api-secret"
```

> **Note:** These are Cloud API Keys (organization-level), not cluster-specific API keys.

### 2. Initialize Terraform

```bash
cd terraform
terraform init
```

### 3. Review the Plan

```bash
terraform plan
```

This will show you all resources that will be created (approximately 200+ resources).

### 4. Apply the Configuration

```bash
terraform apply
```

Type `yes` when prompted. This will take approximately 15-30 minutes to complete.

### 5. View Outputs

```bash
terraform output
```

To view sensitive outputs (API keys):

```bash
terraform output -json | jq
```

## Configuration Options

### Customizing Variables

Create a `terraform.tfvars` file (gitignored by default):

```hcl
environment_name = "my-data-mesh"
cluster_name     = "my-cluster"
cloud_provider   = "AWS"
region           = "us-west-2"
topic_partitions = 3

# Adjust connector behavior
connector_tasks_max          = 2
connector_kafka_max_interval = 500  # Generate messages faster
```

### Available Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `environment_name` | Confluent environment name | `data-mesh-demo` |
| `cluster_name` | Kafka cluster name | `datagen-cluster` |
| `cloud_provider` | Cloud provider (AWS, GCP, AZURE) | `AWS` |
| `region` | Cloud region | `us-east-1` |
| `cluster_availability` | SINGLE_ZONE or MULTI_ZONE | `MULTI_ZONE` |
| `topic_partitions` | Default partitions per topic | `6` |
| `connector_tasks_max` | Max tasks per connector | `1` |
| `connector_kafka_max_interval` | Max ms between messages | `1000` |

## Important Outputs

After applying, Terraform outputs key information for your agents:

```bash
# Cluster connection details
terraform output kafka_bootstrap_endpoint
terraform output schema_registry_rest_endpoint

# Credentials (sensitive)
terraform output cluster_admin_api_key
terraform output cluster_admin_api_secret
terraform output schema_registry_api_key
terraform output schema_registry_api_secret

# Quick overview
terraform output quick_start_info
```

## Architecture

### RBAC Model

This setup uses Confluent Cloud RBAC instead of ACLs:

- **CloudClusterAdmin** role for the admin service account (full cluster access)
- **DeveloperWrite** role for each connector service account (topic write access)
- **DeveloperRead** role for connector monitoring

### Service Accounts

Each datagen connector has its own dedicated service account with minimum required permissions, following the principle of least privilege.

## Cost Considerations

**Standard Cluster:** This uses a Standard cluster (required for RBAC). Approximate costs:

- Standard cluster: ~$1.50/hour base + data transfer
- 38 connectors: ~$0.20/hour each (~$7.60/hour total)
- Schema Registry: ~$0.10/hour

**Estimated total: ~$9-10/hour** or **~$220-240/day** if left running continuously.

### Cost Optimization Tips

1. **Reduce connector count:** Remove unused templates from `var.connector_quickstart_templates`
2. **Pause connectors:** Use Confluent Cloud UI to pause connectors when not in use
3. **Destroy when done:**
   ```bash
   terraform destroy
   ```

## Connecting Your Agents

Once deployed, agents can connect using:

```bash
# Get connection info
BOOTSTRAP_SERVERS=$(terraform output -raw kafka_bootstrap_endpoint)
SCHEMA_REGISTRY_URL=$(terraform output -raw schema_registry_rest_endpoint)
API_KEY=$(terraform output -raw cluster_admin_api_key)
API_SECRET=$(terraform output -raw cluster_admin_api_secret)
```

### Example: List Topics with Confluent CLI

```bash
confluent kafka topic list \
  --bootstrap $BOOTSTRAP_SERVERS \
  --api-key $API_KEY \
  --api-secret $API_SECRET
```

## Troubleshooting

### Issue: API Key errors during apply

**Solution:** Ensure you're using Cloud API Keys (org-level), not cluster API keys.

### Issue: Connector failures

**Solution:** Check RBAC role bindings have propagated. Wait a few minutes and check connector status in Confluent Cloud UI.

### Issue: Schema Registry connection errors

**Solution:** Verify Schema Registry region supports your cloud/region combination.

### Issue: High costs

**Solution:** Run `terraform destroy` when not actively using the demo, or reduce the number of connectors.

## Cleaning Up

To destroy all resources:

```bash
terraform destroy
```

Type `yes` when prompted. This will:
- Delete all 38 connectors
- Delete all topics
- Delete the Kafka cluster
- Delete Schema Registry
- Delete service accounts
- Delete the environment

## Next Steps

With this infrastructure running:

1. **Verify Data Flow:** Check that all 38 connectors are producing data
2. **Deploy Agents:** Configure your autonomous agents to discover and analyze the topics
3. **Monitor Progress:** Watch as agents transform raw streams into organized data products
4. **Iterate:** Adjust connector rates, add/remove topics as needed

## File Structure

```
terraform/
├── .gitignore                  # Ignore state and sensitive files
├── README.md                   # This file
├── main.tf                     # Provider, environment, cluster
├── variables.tf                # Input variables
├── outputs.tf                  # Output values
├── service-accounts.tf         # Service account definitions
├── rbac.tf                     # RBAC role bindings
├── topics.tf                   # Topic definitions
├── schema-registry.tf          # Schema Registry setup
└── datagen-connectors.tf       # Connector configurations
```

## Support

For issues with:
- **Terraform Provider:** https://github.com/confluentinc/terraform-provider-confluent
- **Confluent Cloud:** https://support.confluent.io
- **This Demo:** Create an issue in this repository

## License

This is a demo/reference implementation. Use at your own discretion.
