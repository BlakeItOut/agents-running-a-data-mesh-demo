# Agent Integration Plan: Data Mess to Data Mesh

This document outlines how to integrate autonomous agents using Amazon Bedrock AgentCore with MCP (Model Context Protocol) to transform the raw Confluent Cloud data streams into an organized, product-oriented data mesh.

## Overview

The Agentic Data Mesh Demo uses autonomous agents to:
1. **Discover** raw data streams across 37 Kafka topics
2. **Analyze** data structures, relationships, and usage patterns
3. **Define** bounded contexts and data product boundaries
4. **Generate** data product configurations and documentation
5. **Register** data products in a catalog with governance metadata

## Amazon Bedrock AgentCore + MCP Integration

### What is AgentCore MCP?

Amazon Bedrock AgentCore provides a production-ready runtime for building and deploying AI agents. The MCP (Model Context Protocol) server enables:

- **Conversational Development**: Use natural language to build agents iteratively
- **One-Click Setup**: Integrate with IDEs like Claude Code, Cursor, Amazon Q Developer
- **Built-in Capabilities**: Runtime, gateway integration, identity management, agent memory
- **AWS Integration**: Seamless connection to AWS services and Confluent Cloud

**GitHub Repository**: [awslabs/mcp](https://github.com/awslabs/mcp)
**License**: Apache-2.0

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Development Layer                   │
│  (Claude Code / Cursor / Amazon Q Developer CLI)             │
└──────────────────────┬──────────────────────────────────────┘
                       │ Model Context Protocol (MCP)
┌──────────────────────▼──────────────────────────────────────┐
│              Amazon Bedrock AgentCore                        │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐ │
│  │   Runtime      │  │    Gateway     │  │    Memory     │ │
│  └────────────────┘  └────────────────┘  └───────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  Confluent Cloud                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Environment: agentic-data-mesh                        │ │
│  │  Cluster: data-mesh-cluster (lkc-nd1ng3)               │ │
│  │  - 37 Kafka Topics with Datagen Connectors            │ │
│  │  - Schema Registry (Avro schemas)                     │ │
│  │  - RBAC-enabled access control                        │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Agent Capabilities

### 1. Discovery Agent

**Purpose**: Enumerate and inventory all data streams

**Tools Required**:
- Confluent Cloud API access (Kafka REST API)
- Schema Registry client
- Topic metadata reader

**Outputs**:
- Complete topic inventory with partition counts
- Schema versions and evolution history
- Connector configurations and data sources
- Message volume and throughput metrics

**Implementation**:
```python
# Example capability
async def discover_topics():
    """Enumerate all topics in the cluster"""
    topics = await kafka_admin.list_topics()
    for topic in topics:
        schema = await schema_registry.get_latest_schema(topic)
        metrics = await get_topic_metrics(topic)
        yield TopicInventory(
            name=topic,
            schema=schema,
            partitions=metrics.partitions,
            messages_per_sec=metrics.rate
        )
```

### 2. Analysis Agent

**Purpose**: Understand data structures, relationships, and patterns

**Tools Required**:
- Schema analysis (Avro/JSON parsing)
- Data sampling and profiling
- Relationship detection (foreign key analysis)
- Usage pattern tracking

**Outputs**:
- Data lineage graphs
- Entity relationship diagrams
- Data quality metrics
- Usage frequency heatmaps
- Identified bounded contexts

**Key Analysis Tasks**:
- Detect common fields across topics (e.g., `user_id`, `order_id`)
- Identify potential aggregations (e.g., users + orders = customer activity)
- Classify data domains (financial, e-commerce, gaming, etc.)
- Measure data freshness and completeness

### 3. Product Definition Agent

**Purpose**: Define data products from analyzed streams

**Tools Required**:
- Template generation (for Terraform, documentation)
- Policy definition (access control, retention)
- Metadata creation (tags, descriptions, owners)

**Outputs**:
- Data product specifications (YAML/JSON)
- Access policies and RBAC configurations
- Quality SLAs and monitoring rules
- Documentation (auto-generated markdown)

**Example Data Product**:
```yaml
name: customer-360-view
domain: e-commerce
description: "Unified customer profile combining user data, orders, and ratings"
sources:
  - topic: users
    fields: [id, name, email, region]
  - topic: orders
    fields: [user_id, order_id, total, timestamp]
    join_key: user_id
  - topic: ratings
    fields: [user_id, product_id, rating, review]
    join_key: user_id
transformations:
  - type: join
    strategy: left_outer
  - type: aggregate
    window: 30d
    metrics: [total_orders, avg_rating, lifetime_value]
schema_version: "1.0.0"
owner: data-platform-team
sla:
  freshness: 5m
  completeness: 99.5%
access_policy: read-only-consumers
```

### 4. Catalog Agent

**Purpose**: Register data products in a discoverable catalog

**Tools Required**:
- Data catalog API (e.g., DataHub, Amundsen, AWS Glue)
- Metadata indexing
- Search optimization

**Outputs**:
- Catalog entries with rich metadata
- Searchable data product index
- Lineage tracking
- Usage analytics integration

## Setup Instructions

### Prerequisites

1. **AWS Account** with Bedrock access in supported regions:
   - US East (N. Virginia), US East (Ohio), US West (Oregon)
   - Asia Pacific (Mumbai, Singapore, Sydney, Tokyo)
   - Europe (Frankfurt, Ireland)

2. **Confluent Cloud Infrastructure** (already deployed):
   ```bash
   # Get cluster details
   cd terraform
   terraform output quick_start_info
   ```

3. **AgentCore MCP Server**:
   ```bash
   # Clone the AWS MCP repository
   git clone https://github.com/awslabs/mcp.git
   cd mcp/bedrock-agentcore
   ```

### Installation

```bash
# 1. Install AgentCore MCP server (one-click with npm/pip)
npm install -g @aws/bedrock-agentcore-mcp
# or
pip install bedrock-agentcore-mcp

# 2. Configure with your IDE
# For Claude Code / Cursor:
agentcore-mcp init --ide claude-code

# 3. Set up Confluent Cloud credentials
export KAFKA_BOOTSTRAP_ENDPOINT=$(cd terraform && terraform output -raw kafka_bootstrap_endpoint)
export SCHEMA_REGISTRY_URL=$(cd terraform && terraform output -raw schema_registry_rest_endpoint)
export KAFKA_API_KEY=$(cd terraform && terraform output -raw cluster_admin_api_key)
export KAFKA_API_SECRET=$(cd terraform && terraform output -raw cluster_admin_api_secret)

# 4. Configure AgentCore with Confluent access
agentcore-mcp configure --service confluent-cloud \
  --bootstrap-server $KAFKA_BOOTSTRAP_ENDPOINT \
  --api-key $KAFKA_API_KEY \
  --api-secret $KAFKA_API_SECRET \
  --schema-registry $SCHEMA_REGISTRY_URL
```

### Agent Development Workflow

Using AgentCore MCP, you can develop agents conversationally:

```
User (via Claude Code):
"Create a discovery agent that lists all topics in the agentic-data-mesh cluster
and retrieves their schemas from Schema Registry"

AgentCore MCP:
✓ Generating agent scaffold
✓ Adding Confluent Cloud connector
✓ Integrating Schema Registry client
✓ Creating discovery logic
✓ Agent ready: discovery-agent-v1

Would you like to deploy to development environment?

User: "Yes, deploy and run it"

AgentCore MCP:
✓ Deployed to AWS Lambda
✓ Executing discovery...
✓ Found 37 topics
✓ Retrieved 37 schemas
✓ Results saved to S3: s3://data-mesh-agents/discovery/run-001/
```

## Data Mesh Transformation Process

### Phase 1: Discovery (Days 1-2)

**Goal**: Complete inventory of all raw data

**Agent Actions**:
1. Enumerate all 37 topics
2. Extract schemas from Schema Registry
3. Sample data from each stream (first 100 messages)
4. Collect connector configurations
5. Measure message rates and volumes

**Deliverable**: `data-inventory.json` with complete catalog

### Phase 2: Analysis (Days 3-5)

**Goal**: Understand relationships and identify data products

**Agent Actions**:
1. Parse all Avro schemas
2. Detect common fields and join keys
3. Identify bounded contexts (domains)
4. Profile data quality metrics
5. Map data lineage

**Deliverables**:
- `entity-relationships.graphml` (ER diagram)
- `bounded-contexts.yaml` (domain definitions)
- `data-quality-report.md`

### Phase 3: Product Definition (Days 6-8)

**Goal**: Define and document data products

**Agent Actions**:
1. Generate data product specifications
2. Create transformation logic (joins, aggregations)
3. Define access policies and SLAs
4. Auto-generate documentation
5. Create monitoring dashboards

**Deliverables**:
- `data-products/*.yaml` (product specifications)
- `docs/data-products/*.md` (documentation)
- `terraform/data-products/*.tf` (infrastructure)

### Phase 4: Registration (Days 9-10)

**Goal**: Publish to data catalog

**Agent Actions**:
1. Create catalog entries
2. Index metadata for search
3. Establish lineage links
4. Configure access controls
5. Enable discovery UIs

**Deliverable**: Searchable data catalog with all products

## Integration with Existing Infrastructure

### Terraform Outputs for Agents

Agents can retrieve cluster information programmatically:

```bash
# Export all outputs as JSON for agent consumption
terraform output -json > terraform-outputs.json
```

```python
# Agent code example
import json

with open('terraform-outputs.json') as f:
    config = json.load(f)

KAFKA_ENDPOINT = config['kafka_bootstrap_endpoint']['value']
SCHEMA_REGISTRY = config['schema_registry_rest_endpoint']['value']
TOPICS = config['topic_names']['value']  # List of 37 topics
```

### Using Existing Service Accounts

The Terraform setup created 38 service accounts. Agents can use the admin account for full access:

```python
from confluent_kafka import admin

admin_client = admin.AdminClient({
    'bootstrap.servers': KAFKA_ENDPOINT,
    'sasl.mechanisms': 'PLAIN',
    'security.protocol': 'SASL_SSL',
    'sasl.username': config['cluster_admin_api_key']['value'],
    'sasl.password': config['cluster_admin_api_secret']['value']
})
```

## Agent Memory and State Management

AgentCore provides built-in memory for maintaining context across runs:

```python
# Example: Store analysis results
await agent.memory.store('topic_analysis', {
    'topic': 'users',
    'domain': 'e-commerce',
    'quality_score': 0.95,
    'relationships': ['orders', 'ratings']
})

# Later: Retrieve for product definition
user_analysis = await agent.memory.retrieve('topic_analysis')
```

## Cost Considerations

### AgentCore Runtime Costs

- **Lambda executions**: ~$0.20 per million requests
- **Bedrock model usage**: Variable by model (Claude, etc.)
- **S3 storage**: ~$0.023/GB for agent outputs

### Confluent Cloud Costs (Reminder)

Running infrastructure: ~$9-10/hour (~$220-240/day)

**Cost Optimization**: Run agents during active development, then destroy infrastructure when not in use.

## Security Best Practices

1. **Credential Management**:
   - Store Confluent API keys in AWS Secrets Manager
   - Use IAM roles for AgentCore service permissions
   - Rotate credentials regularly

2. **Access Control**:
   - Agents use dedicated service accounts (not admin)
   - Apply least-privilege RBAC policies
   - Audit all agent actions via CloudTrail

3. **Data Privacy**:
   - Agents sample data (don't persist full streams)
   - PII detection and masking in analysis phase
   - Compliance with data governance policies

## Next Steps

1. **Set up AgentCore MCP** following installation instructions above
2. **Develop Discovery Agent** to inventory the 37 topics
3. **Run Analysis Phase** to identify data product candidates
4. **Generate Product Specs** using Product Definition Agent
5. **Deploy Catalog** and publish data products
6. **Monitor & Iterate** as new data streams are added

## References

- [Amazon Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock-agentcore/)
- [Model Context Protocol Spec](https://github.com/awslabs/mcp)
- [Confluent Cloud REST API](https://docs.confluent.io/cloud/current/api.html)
- [Data Mesh Principles](https://martinfowler.com/articles/data-mesh-principles.html)

## Support

For questions about this integration:
- **Terraform infrastructure**: See `terraform/README.md`
- **Agent development**: AWS Bedrock AgentCore support
- **Confluent Cloud**: https://support.confluent.io
