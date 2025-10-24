# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository demonstrates autonomous agents transforming raw, stream-based data into a product-oriented, discoverable data mesh. The demo creates a realistic "raw data mess" in Confluent Cloud with 37 different datagen connectors producing continuous sample data across multiple domains (financial, e-commerce, gaming, fleet management, etc.), which agents will analyze and organize into structured data products.

## Architecture

### Infrastructure Layer (Terraform)

The entire data environment is provisioned via Terraform in the `terraform/` directory:

- **Environment & Cluster**: Creates a Confluent Cloud environment with Stream Governance (ESSENTIALS package) and a Standard Kafka cluster (required for RBAC support)
- **37 Kafka Topics**: One per datagen template, with configurable partitions (default: 6) and retention (default: 7 days)
- **Schema Registry**: Managed service with Avro schemas for all topics, integrated via Stream Governance
- **Service Accounts**: 38 total (1 admin + 37 connector-specific), following principle of least privilege
- **RBAC Model**: Uses Confluent Cloud RBAC instead of ACLs
  - `CloudClusterAdmin` role for admin service account
  - `DeveloperWrite` role for connector write access
  - `DeveloperRead` role for connector monitoring
- **37 Datagen Connectors**: Continuously generate sample data at configurable intervals (default: 1 message/second)

### Terraform File Structure

- `main.tf`: Provider config, environment, cluster, and admin service account
- `variables.tf`: All configurable inputs (cloud provider, region, connector templates list, etc.)
- `outputs.tf`: Connection details, credentials, and quick start info for agents
- `service-accounts.tf`: Per-connector service account definitions
- `rbac.tf`: Role bindings for all service accounts
- `topics.tf`: Topic creation for all datagen templates
- `schema-registry.tf`: Schema Registry data source and API key creation
- `datagen-connectors.tf`: Connector configurations using quickstart templates

### Agent Integration Points

When agents are implemented, they will connect using outputs from Terraform:

- **Bootstrap Endpoint**: `terraform output kafka_bootstrap_endpoint`
- **Schema Registry**: `terraform output schema_registry_rest_endpoint`
- **Credentials**: `terraform output -json` for API keys/secrets (sensitive)
- **Topic List**: `terraform output topic_names`

Agents should analyze data streams, leverage Schema Registry metadata, identify usage patterns, and autonomously define data products with appropriate configurations.

## Common Commands

### Environment Setup

```bash
# Set Confluent Cloud credentials (use Cloud API Keys, not cluster-specific keys)
export CONFLUENT_CLOUD_API_KEY="your-api-key-here"
export CONFLUENT_CLOUD_API_SECRET="your-api-secret-here"

# Or use .env file (recommended)
cp .env.example .env
# Edit .env with your credentials
source .env
```

### Terraform Operations

```bash
cd terraform

# Initialize Terraform (downloads Confluent provider ~> 2.0)
terraform init

# Review what will be created (~190+ resources)
terraform plan

# Deploy infrastructure (takes 15-30 minutes)
terraform apply

# Quick approval without confirmation prompt
terraform apply -auto-approve

# View connection info for agents
terraform output quick_start_info

# View sensitive credentials
terraform output -json | jq

# Destroy all resources (important for cost management)
terraform destroy
```

### Customizing the Deployment

Create `terraform/terraform.tfvars` to override defaults:

```hcl
environment_name = "my-data-mesh"
cluster_name     = "my-cluster"
cloud_provider   = "AWS"
region           = "us-west-2"
topic_partitions = 3
connector_kafka_max_interval = 500  # Faster message generation
```

### Cost Management

The Standard cluster costs approximately $9-10/hour or $220-240/day if left running. To minimize costs:

```bash
# Pause connectors via Confluent Cloud UI when not in use
# OR destroy the entire environment when done
terraform destroy
```

To reduce connector count, edit `var.connector_quickstart_templates` in `variables.tf`.

## Important Implementation Details

### Credential Types

**Critical**: This setup requires **Cloud API Keys** (organization-level) from Confluent Cloud Console > Cloud API Keys, NOT cluster-specific API keys. Cloud API Keys work across all environments and clusters.

### Resource Creation Timing

- Total terraform apply: 15-20 minutes
- API keys: 2+ minutes each (created in batches)
- Connectors may retry initially if topics aren't immediately ready (expected behavior)

### RBAC Propagation

After `terraform apply`, RBAC role bindings may take a few minutes to propagate. If connectors show failures, wait and check status in Confluent Cloud UI.

### Terraform State

State files contain sensitive credentials. The `.gitignore` properly excludes:
- `*.tfstate`
- `*.tfstate.*`
- `.terraform/`
- `.env`

Never commit these files.

## Datagen Templates

The 37 templates span diverse domains to create realistic complexity:

- **Financial/Trading** (4): campaign_finance, credit_cards, stock_trades, transactions
- **E-commerce/Retail** (9): inventory, orders, product, purchases, ratings, shoe_clickstream, shoe_customers, shoe_orders, shoes, stores
- **Pizza Delivery** (3): pizza_orders, pizza_orders_cancelled, pizza_orders_completed
- **Web Analytics** (4): clickstream, clickstream_codes, clickstream_users, pageviews
- **Users** (1): users
- **Gaming** (3): gaming_games, gaming_players, gaming_player_activity
- **Insurance** (3): insurance_customers, insurance_offers, insurance_customer_activity
- **Fleet Management** (3): fleet_mgmt_location, fleet_mgmt_sensors, fleet_mgmt_description
- **HR/Payroll** (3): payroll_employee, payroll_employee_location, payroll_bonus
- **Security/Logging** (2): siem_logs, syslog_logs
- **IoT** (1): device_information

## Current State

This repository is in **Phase 1** (Foundational Setup). The Terraform infrastructure is complete and functional.

**Next: Agent Integration** - See `AGENTS.md` for detailed documentation on integrating Amazon Bedrock AgentCore with MCP (Model Context Protocol) to automate the data mesh transformation.

Future phases will implement:

1. **Autonomous Agents** (via Amazon Bedrock AgentCore MCP)
   - Discovery Agent: Enumerate and inventory all data streams
   - Analysis Agent: Understand relationships and patterns
   - Product Definition Agent: Define data products from analyzed streams
   - Catalog Agent: Register products in discoverable catalog
2. Analysis and enrichment using Schema Registry and usage metrics
3. Data product definition and registration
4. Presentation materials and self-guided demo

## Git Workflow

Current branch: `main` (also the default branch for PRs)

Recent changes focus on Terraform configuration for Confluent Cloud setup, including Schema Registry integration and RBAC configuration.
