# Confluent Cloud Data Mesh Demo - Terraform Setup

This Terraform configuration spins up a complete Confluent Cloud environment with all 37 datagen connector templates, creating a realistic "raw data mess" for autonomous agents to organize into a data mesh.

## Overview

This setup creates:

- **1 Confluent Cloud Environment** (`agentic-data-mesh`)
- **1 Standard Kafka Cluster** (multi-zone, RBAC-enabled)
- **37 Kafka Topics** (one per datagen template)
- **Schema Registry** with Avro schemas for all topics
- **37 Datagen Connectors** generating continuous sample data
- **38 Service Accounts** (1 admin + 37 connector-specific)
- **RBAC Role Bindings** (DeveloperWrite/DeveloperRead roles)

### Datagen Templates Included

The setup includes all available Confluent datagen quickstart templates across multiple domains:

**Financial/Trading (4):** campaign_finance, credit_cards, stock_trades, transactions

**E-commerce/Retail (9):** inventory, orders, product, purchases, ratings, shoe_clickstream, shoe_customers, shoe_orders, shoes, stores

**Pizza Delivery (3):** pizza_orders, pizza_orders_cancelled, pizza_orders_completed

**Web Analytics (4):** clickstream, clickstream_codes, clickstream_users, pageviews

**Users (1):** users

**Gaming (3):** gaming_games, gaming_players, gaming_player_activity

**Insurance (3):** insurance_customers, insurance_offers, insurance_customer_activity

**Fleet Management (3):** fleet_mgmt_location, fleet_mgmt_sensors, fleet_mgmt_description

**HR/Payroll (3):** payroll_employee, payroll_employee_location, payroll_bonus

**Security/Logging (2):** siem_logs, syslog_logs

**IoT (1):** device_information

## Prerequisites

1. **Confluent Cloud Account**
   - Sign up at https://confluent.cloud
   - **Payment method required** (even with free credits, add a credit card at Account & Billing > Payment methods)
   - Create Cloud API credentials (not cluster-specific) - see detailed instructions below

2. **Terraform**
   - Install Terraform >= 1.0
   - https://www.terraform.io/downloads

3. **Environment Variables**
   ```bash
   export CONFLUENT_CLOUD_API_KEY="<your-api-key>"
   export CONFLUENT_CLOUD_API_SECRET="<your-api-secret>"
   ```

### Getting Cloud API Keys (First Time Users)

If this is your first time setting up Confluent Cloud API keys:

1. **Log into Confluent Cloud** at https://confluent.cloud
2. **Navigate to Cloud API Keys:**
   - Click on your profile/organization icon in the top right corner
   - Select "Cloud API Keys" from the dropdown menu
3. **Create a new Cloud API key:**
   - Click "Add key" or "Create key"
   - Choose **"My account"** (not "Service account") for simplest setup
   - Give it a description like "terraform-agentic-data-mesh"
   - **Important:** Copy both the key and secret immediately - you won't see the secret again!
4. **Set environment variables:**

   **Option A: Direct export (temporary, current shell only)**
   ```bash
   export CONFLUENT_CLOUD_API_KEY="<your-key>"
   export CONFLUENT_CLOUD_API_SECRET="<your-secret>"
   ```

   **Option B: Use .env file (recommended for local development)**
   ```bash
   # From the repository root
   cp .env.example .env

   # Edit .env with your actual credentials
   # Then source it
   source .env
   ```

> **Important Note:** These are **Cloud API Keys** (organization-level) that work across all environments and clusters. They are different from cluster-specific API keys that you might create later.

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

This will show you all resources that will be created (approximately 190+ resources).

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

## Step-by-Step First Run Guide

For users new to Confluent Cloud and Terraform, here's a complete walkthrough:

```bash
# 1. Clone the repository
git clone <repo-url>
cd agents-running-a-data-mesh-demo

# 2. Set up credentials (choose one method)

# Method A: Direct export
export CONFLUENT_CLOUD_API_KEY="<your-key>"
export CONFLUENT_CLOUD_API_SECRET="<your-secret>"

# Method B: Use .env file (recommended)
cp .env.example .env
# Edit .env with your credentials using your preferred editor
source .env

# 3. Navigate to terraform directory
cd terraform

# 4. Initialize Terraform (downloads providers)
terraform init

# 5. Review what will be created
terraform plan
# You should see approximately 190+ resources to be created

# 6. Apply the configuration
terraform apply -auto-approve
# Or use 'terraform apply' without -auto-approve to review and confirm manually

# 7. Wait 15-20 minutes for completion
# You can monitor progress in the Confluent Cloud console

# 8. View your cluster details
terraform output quick_start_info

# 9. Get sensitive credentials (for agents)
terraform output -json | jq
```

**Expected Timeline:**
- Initial setup & terraform init: 2-3 minutes
- Terraform apply execution: 15-20 minutes
- **Total: ~20-25 minutes from start to finish**

### Monitoring Your Apply

While terraform is running, you can monitor progress:

**Check Confluent Cloud Console:**
- Navigate to https://confluent.cloud
- Go to your environment (will appear as "agentic-data-mesh")
- Watch resources appear in real-time as they're created

**Monitor Terraform Progress (if using logs):**
```bash
# In another terminal, watch the terraform output
tail -f /tmp/terraform-apply.log

# Count completed resources
grep -c "Creation complete" /tmp/terraform-apply.log
```

**Resource Creation Order:**
1. Environment & Cluster (1-2 minutes)
2. Service Accounts (quick, ~30 seconds)
3. API Keys (2 minutes each, created in batches of 10)
4. Topics (quick, all created together in ~10 seconds)
5. RBAC Role Bindings (1-2 minutes)
6. Connectors (2-3 minutes total, some may retry if topics aren't ready)

**Progress Indicators:**
- ~70 resources = Environment, cluster, accounts, and most API keys complete
- ~135 resources = All topics and role bindings complete
- ~175 resources = Most connectors created
- ~190 resources = Complete!

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
| `environment_name` | Confluent environment name | `agentic-data-mesh` |
| `cluster_name` | Kafka cluster name | `data-mesh-cluster` |
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
- 37 connectors: ~$0.20/hour each (~$7.40/hour total)
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

### Common Issues During Setup

#### Payment Method Required
**Error:** "402 Payment Required: Forbidden: No credit card on file"

**Solution:** Even with free credits, Confluent Cloud requires a payment method on file to create Standard clusters.
- Add a credit card at: Confluent Cloud Console > Account & Billing > Payment methods
- Your free credits will still be used first
- You won't be charged unless you exceed your credits

#### Terraform State Lock
**Error:** "Error acquiring the state lock" or "resource temporarily unavailable"

**Solution:** If terraform crashes or is interrupted, a lock file may remain.
```bash
# Remove the lock file
rm -f .terraform.tfstate.lock.info

# Then retry your terraform command
terraform apply
```

#### API Key Permissions Error
**Error:** "403 Forbidden" or "401 Unauthorized" during apply

**Solution:** Ensure you're using the correct type of API keys.
- Use **Cloud API Keys** (organization-level) from Cloud settings
- NOT cluster-specific API keys
- If using a service account key, ensure it has OrganizationAdmin permissions
- **Recommended:** Use "My account" Cloud API keys for simplest setup

#### Slow Resource Creation
**Not an error, but expected behavior:**
- API keys take 2+ minutes each to create (they're created in batches)
- Total terraform apply time: 15-20 minutes for all 190+ resources
- **Do not interrupt** the terraform process - let it complete
- You can monitor progress in the Confluent Cloud console

#### Credentials Not Working
**Error:** API key not recognized or authentication failures

**Solution:**
- Verify you're using **Cloud API Keys** (from organization settings)
- NOT cluster-specific API keys
- Ensure environment variables are exported in your current shell session
- If using .env file, make sure you ran `source .env`
- Test with: `echo $CONFLUENT_CLOUD_API_KEY` (should display your key)

### Other Issues

#### Connector Failures After Apply

**Solution:** Check RBAC role bindings have propagated. Wait a few minutes and check connector status in Confluent Cloud UI. Some connectors may take a moment to start after topics are created.

#### Schema Registry Connection Errors

**Solution:** Verify Schema Registry region supports your cloud/region combination. The configuration uses us-east-1 AWS by default.

#### High Costs

**Solution:** Run `terraform destroy` when not actively using the demo, or reduce the number of connectors by modifying the `connector_quickstart_templates` variable.

## Cleaning Up

To destroy all resources:

```bash
terraform destroy
```

Type `yes` when prompted. This will:
- Delete all 37 connectors
- Delete all topics
- Delete the Kafka cluster
- Delete Schema Registry
- Delete service accounts
- Delete the environment

## Next Steps

With this infrastructure running:

1. **Verify Data Flow:** Check that all 37 connectors are producing data
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
