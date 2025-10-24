# Discovery Agent Implementation Plan

## Overview

Build a Discovery Agent that uses the official **Confluent MCP Server** (released April 2025) to inventory all 37 Kafka topics, schemas, and connectors in the `agentic-data-mesh` environment.

**Key Technology**: [confluentinc/mcp-confluent](https://github.com/confluentinc/mcp-confluent) - Official Confluent MCP server that enables AI assistants to interact with Confluent Cloud REST API using natural language.

## Architecture

```
┌─────────────────────────────────────────────────┐
│   Claude Code / AI Assistant                    │
│   (Natural Language Interface)                  │
└────────────────┬────────────────────────────────┘
                 │ Model Context Protocol (MCP)
┌────────────────▼────────────────────────────────┐
│   Confluent MCP Server (Node.js 22)             │
│   - Topic management tools                      │
│   - Connector management tools                  │
│   - Flink SQL tools                             │
│   - Schema Registry integration                 │
└────────────────┬────────────────────────────────┘
                 │ Confluent Cloud REST API
┌────────────────▼────────────────────────────────┐
│   Confluent Cloud                               │
│   Environment: agentic-data-mesh                │
│   Cluster: data-mesh-cluster (lkc-nd1ng3)       │
│   - 37 Kafka Topics                             │
│   - 37 Datagen Connectors                       │
│   - Schema Registry                             │
└─────────────────────────────────────────────────┘
```

## Phase 1: Terraform - Agent Service Account & Permissions

### New Terraform Resources to Add

Create `terraform/agents.tf` with:

```hcl
# Discovery Agent Service Account
resource "confluent_service_account" "discovery_agent" {
  display_name = "discovery-agent"
  description  = "Service account for Discovery Agent to inventory topics and connectors"
}

# API Key for Discovery Agent (cluster access)
resource "confluent_api_key" "discovery_agent_cluster_key" {
  display_name = "discovery-agent-cluster-api-key"
  description  = "Cluster API Key for Discovery Agent"

  owner {
    id          = confluent_service_account.discovery_agent.id
    api_version = confluent_service_account.discovery_agent.api_version
    kind        = confluent_service_account.discovery_agent.kind
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

# API Key for Discovery Agent (Schema Registry access)
resource "confluent_api_key" "discovery_agent_sr_key" {
  display_name = "discovery-agent-sr-api-key"
  description  = "Schema Registry API Key for Discovery Agent"

  owner {
    id          = confluent_service_account.discovery_agent.id
    api_version = confluent_service_account.discovery_agent.api_version
    kind        = confluent_service_account.discovery_agent.kind
  }

  managed_resource {
    id          = data.confluent_schema_registry_cluster.schema_registry.id
    api_version = data.confluent_schema_registry_cluster.schema_registry.api_version
    kind        = data.confluent_schema_registry_cluster.schema_registry.kind

    environment {
      id = confluent_environment.data_mesh_env.id
    }
  }

  lifecycle {
    prevent_destroy = false
  }
}

# RBAC: Grant DeveloperRead on all topics
resource "confluent_role_binding" "discovery_agent_read_topics" {
  principal   = "User:${confluent_service_account.discovery_agent.id}"
  role_name   = "DeveloperRead"
  crn_pattern = "${confluent_kafka_cluster.datagen_cluster.rbac_crn}/kafka=${confluent_kafka_cluster.datagen_cluster.id}/topic=*"

  lifecycle {
    prevent_destroy = false
  }
}

# RBAC: Grant CloudClusterAdmin for connector/cluster metadata access
# Note: Could use more restrictive role, but CloudClusterAdmin ensures full read access
resource "confluent_role_binding" "discovery_agent_cluster_admin" {
  principal   = "User:${confluent_service_account.discovery_agent.id}"
  role_name   = "CloudClusterAdmin"
  crn_pattern = confluent_kafka_cluster.datagen_cluster.rbac_crn

  lifecycle {
    prevent_destroy = false
  }
}

# Output agent credentials for MCP configuration
output "discovery_agent_cluster_api_key" {
  description = "Discovery Agent cluster API key"
  value       = confluent_api_key.discovery_agent_cluster_key.id
  sensitive   = true
}

output "discovery_agent_cluster_api_secret" {
  description = "Discovery Agent cluster API secret"
  value       = confluent_api_key.discovery_agent_cluster_key.secret
  sensitive   = true
}

output "discovery_agent_sr_api_key" {
  description = "Discovery Agent Schema Registry API key"
  value       = confluent_api_key.discovery_agent_sr_key.id
  sensitive   = true
}

output "discovery_agent_sr_api_secret" {
  description = "Discovery Agent Schema Registry API secret"
  value       = confluent_api_key.discovery_agent_sr_key.secret
  sensitive   = true
}
```

### Apply Terraform Changes

```bash
cd terraform
terraform plan -target=module.agents  # Review agent-specific changes
terraform apply -target=module.agents # Apply agent resources only
```

## Phase 2: Confluent MCP Server Setup

### Prerequisites

- Node.js 22+ installed
- Terraform outputs available

### Installation Steps

1. **Create agent directory structure**:
   ```bash
   mkdir -p agents/discovery
   cd agents/discovery
   ```

2. **Clone/Install Confluent MCP**:
   ```bash
   # Option A: Clone from GitHub
   git clone https://github.com/confluentinc/mcp-confluent.git
   cd mcp-confluent
   npm install

   # Option B: Install via npm (if published)
   npm install -g @confluentinc/mcp-confluent
   ```

3. **Create MCP Configuration**:

   File: `agents/discovery/mcp-config.json`

   ```json
   {
     "mcpServers": {
       "confluent": {
         "command": "node",
         "args": ["path/to/mcp-confluent/build/index.js"],
         "env": {
           "CONFLUENT_CLOUD_API_KEY": "discovery_agent_cloud_api_key",
           "CONFLUENT_CLOUD_API_SECRET": "discovery_agent_cloud_api_secret",
           "CONFLUENT_ENVIRONMENT_ID": "env-7zpqx1",
           "CONFLUENT_KAFKA_CLUSTER_ID": "lkc-nd1ng3",
           "CONFLUENT_SCHEMA_REGISTRY_ID": "from_terraform_output",
           "KAFKA_BOOTSTRAP_ENDPOINT": "from_terraform_output",
           "SCHEMA_REGISTRY_ENDPOINT": "from_terraform_output"
         }
       }
     }
   }
   ```

4. **Populate from Terraform**:

   Create: `agents/discovery/configure-mcp.sh`

   ```bash
   #!/bin/bash
   # Populate MCP config from Terraform outputs

   cd ../../terraform

   # Export all needed values
   export ENVIRONMENT_ID=$(terraform output -raw environment_id)
   export CLUSTER_ID=$(terraform output -raw kafka_cluster_id)
   export KAFKA_ENDPOINT=$(terraform output -raw kafka_bootstrap_endpoint)
   export SR_ENDPOINT=$(terraform output -raw schema_registry_rest_endpoint)
   export SR_ID=$(terraform output -raw schema_registry_id)

   export AGENT_CLUSTER_KEY=$(terraform output -raw discovery_agent_cluster_api_key)
   export AGENT_CLUSTER_SECRET=$(terraform output -raw discovery_agent_cluster_api_secret)
   export AGENT_SR_KEY=$(terraform output -raw discovery_agent_sr_api_key)
   export AGENT_SR_SECRET=$(terraform output -raw discovery_agent_sr_api_secret)

   cd ../agents/discovery

   # Create .env file for MCP server
   cat > .env <<EOF
   CONFLUENT_CLOUD_API_KEY=${AGENT_CLUSTER_KEY}
   CONFLUENT_CLOUD_API_SECRET=${AGENT_CLUSTER_SECRET}
   CONFLUENT_ENVIRONMENT_ID=${ENVIRONMENT_ID}
   CONFLUENT_KAFKA_CLUSTER_ID=${CLUSTER_ID}
   CONFLUENT_SCHEMA_REGISTRY_ID=${SR_ID}
   KAFKA_BOOTSTRAP_ENDPOINT=${KAFKA_ENDPOINT}
   SCHEMA_REGISTRY_ENDPOINT=${SR_ENDPOINT}
   SCHEMA_REGISTRY_API_KEY=${AGENT_SR_KEY}
   SCHEMA_REGISTRY_API_SECRET=${AGENT_SR_SECRET}
   EOF

   echo "MCP configuration complete! Credentials stored in .env"
   ```

   ```bash
   chmod +x configure-mcp.sh
   ./configure-mcp.sh
   ```

## Phase 3: Discovery Agent Workflow

### Available MCP Tools (from Confluent MCP Server)

Based on the Confluent MCP server capabilities:

1. **Topic Management**:
   - `list_topics` - List all Kafka topics
   - `describe_topic` - Get topic details (partitions, configs)
   - `get_topic_configs` - Retrieve topic configuration

2. **Connector Management**:
   - `list_connectors` - List all connectors
   - `describe_connector` - Get connector details and status
   - `get_connector_config` - Retrieve connector configuration

3. **Schema Registry**:
   - `list_schemas` - List all schemas
   - `get_schema` - Retrieve specific schema version
   - `describe_schema` - Get schema metadata

4. **Flink SQL** (if needed):
   - `execute_flink_sql` - Run Flink SQL queries
   - `list_flink_statements` - View Flink statement history

### Discovery Workflow Script

Create: `agents/discovery/run-discovery.py`

```python
#!/usr/bin/env python3
"""
Discovery Agent using Confluent MCP
Inventories all topics, schemas, and connectors
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

def run_mcp_command(tool_name, parameters=None):
    """Execute MCP tool via Claude Code or direct MCP invocation"""
    # This would integrate with MCP SDK or Claude Code API
    # For now, pseudocode showing the flow
    pass

def discover_topics():
    """Discover all Kafka topics"""
    print("Discovering topics...")
    topics = run_mcp_command("list_topics")

    topic_details = []
    for topic in topics:
        details = run_mcp_command("describe_topic", {"topic_name": topic})
        config = run_mcp_command("get_topic_configs", {"topic_name": topic})
        topic_details.append({
            "name": topic,
            "details": details,
            "config": config
        })

    return topic_details

def discover_schemas():
    """Discover all Schema Registry schemas"""
    print("Discovering schemas...")
    schemas = run_mcp_command("list_schemas")

    schema_details = []
    for schema_subject in schemas:
        schema = run_mcp_command("get_schema", {"subject": schema_subject})
        schema_details.append(schema)

    return schema_details

def discover_connectors():
    """Discover all connectors"""
    print("Discovering connectors...")
    connectors = run_mcp_command("list_connectors")

    connector_details = []
    for connector in connectors:
        details = run_mcp_command("describe_connector", {"connector_name": connector})
        config = run_mcp_command("get_connector_config", {"connector_name": connector})
        connector_details.append({
            "name": connector,
            "details": details,
            "config": config
        })

    return connector_details

def main():
    """Run full discovery"""
    output_dir = Path("./discovery-outputs")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.utcnow().isoformat()

    inventory = {
        "environment": "agentic-data-mesh",
        "cluster": "data-mesh-cluster",
        "discovery_timestamp": timestamp,
        "topics": discover_topics(),
        "schemas": discover_schemas(),
        "connectors": discover_connectors()
    }

    # Save inventory
    output_file = output_dir / f"inventory-{timestamp}.json"
    with open(output_file, 'w') as f:
        json.dump(inventory, f, indent=2)

    print(f"Discovery complete! Inventory saved to {output_file}")
    print(f"Found {len(inventory['topics'])} topics")
    print(f"Found {len(inventory['schemas'])} schemas")
    print(f"Found {len(inventory['connectors'])} connectors")

if __name__ == "__main__":
    main()
```

### Using Claude Code with MCP

Alternatively, interact conversationally:

```
User (in Claude Code with MCP configured):
"List all Kafka topics in the agentic-data-mesh environment"

Claude (via Confluent MCP):
✓ Connected to Confluent Cloud
✓ Environment: env-7zpqx1 (agentic-data-mesh)
✓ Cluster: lkc-nd1ng3 (data-mesh-cluster)

Found 37 topics:
1. campaign_finance (6 partitions)
2. clickstream (6 partitions)
3. clickstream_codes (6 partitions)
...
37. users (6 partitions)

User: "Get the Avro schema for the 'users' topic"

Claude (via MCP):
✓ Retrieved schema from Schema Registry
Schema version: 1
Type: AVRO
{
  "type": "record",
  "name": "users",
  "fields": [...]
}
```

## Phase 4: Expected Outputs

### Directory Structure

```
agents/
└── discovery/
    ├── README.md                    # Setup and usage instructions
    ├── mcp-config.json              # MCP server configuration
    ├── configure-mcp.sh             # Script to populate config from Terraform
    ├── .env                         # Credentials (gitignored)
    ├── .gitignore                   # Ignore .env and outputs
    ├── run-discovery.py             # Discovery automation script
    └── discovery-outputs/
        └── inventory-2025-10-24.json  # Discovery results
```

### Inventory Output Format

```json
{
  "environment": "agentic-data-mesh",
  "cluster": "data-mesh-cluster",
  "discovery_timestamp": "2025-10-24T02:30:00Z",
  "topics": [
    {
      "name": "users",
      "details": {
        "partitions": 6,
        "replication_factor": 3,
        "cleanup_policy": "delete"
      },
      "config": {
        "retention.ms": "604800000",
        "segment.ms": "86400000"
      },
      "schema": {
        "version": 1,
        "type": "AVRO",
        "fields": [...]
      }
    },
    // ... 36 more topics
  ],
  "connectors": [
    {
      "name": "DatagenSourceConnector_users",
      "type": "SOURCE",
      "status": "RUNNING",
      "config": {
        "connector.class": "DatagenSource",
        "kafka.topic": "users",
        "quickstart": "USERS"
      }
    },
    // ... 36 more connectors
  ],
  "summary": {
    "total_topics": 37,
    "total_partitions": 222,
    "total_connectors": 37,
    "active_connectors": 37
  }
}
```

## Phase 5: Amazon Bedrock AgentCore Agent Implementation

This phase creates a production-ready autonomous agent using Amazon Bedrock AgentCore Runtime, deploying it as an event-driven service that publishes complete cluster snapshots to Kafka.

### Overview: AgentCore vs Claude Code Interface

**Claude Code Interface** (Phase 3):
- Interactive conversational development
- Manual MCP tool invocation
- Developer-driven workflow
- Great for prototyping and exploration

**Amazon Bedrock AgentCore Agent** (This Phase):
- Autonomous, event-driven execution
- Production-ready runtime
- Triggered by cluster changes and anomalies
- Publishes to Kafka (event-carried state pattern)

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 Event Triggers                           │
│  - Schema Registry changes (new versions)                │
│  - Metrics anomalies (CloudWatch Alarms)                 │
│  - Connector failures (status changes)                   │
│  - New resources created (topics/connectors)             │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│        Discovery Agent (AWS Lambda)                      │
│  ┌───────────────────────────────────────────────────┐  │
│  │  BedrockAgentCoreApp()                            │  │
│  │  - Agent Runtime                                  │  │
│  │  - Tool Orchestration (MCP)                       │  │
│  │  - Kafka Producer                                 │  │
│  └───────────────┬───────────────────────────────────┘  │
└──────────────────┼──────────────────────────────────────┘
                   │ MCP          │ Kafka Producer
       ┌───────────▼──────┐       │
       │                  │       │
┌──────▼──────────────────▼───────▼─────────────────────┐
│          Confluent Cloud                               │
│  ┌─────────────────────────────────────────────────┐  │
│  │  Confluent MCP Server (tools)                   │  │
│  │  - list_topics, describe_topic                  │  │
│  │  - list_connectors, describe_connector          │  │
│  │  - list_schemas, get_schema                     │  │
│  │  - get_consumer_groups, get_metrics             │  │
│  └─────────────────────────────────────────────────┘  │
│                                                        │
│  ┌─────────────────────────────────────────────────┐  │
│  │  Discovery Events Topic (log compacted)         │  │
│  │  Key: cluster_id                                │  │
│  │  Value: Complete cluster snapshot (Avro)        │  │
│  │  - All topics, connectors, schemas              │  │
│  │  - Consumer groups, metrics                     │  │
│  │  - Trigger info (what changed)                  │  │
│  └─────────────────────────────────────────────────┘  │
│                                                        │
│  Environment: agentic-data-mesh                        │
│  Cluster: data-mesh-cluster                            │
└────────────────────────────────────────────────────────┘
```

### Event-Carried State Pattern

**Pattern:** Each message in `discovery-events` contains the complete current state of the cluster.

**Benefits:**
- Consumers get everything they need in one message (no joins, no lookups)
- With 200K token context windows, 37 topics with schemas ≈ 50-100K tokens
- Topic compaction keeps only latest snapshot (automatic state management)
- Trigger field explains what changed (for logging/debugging)

**Schema:**
```json
{
  "discovery_timestamp": "2025-10-24T10:15:00Z",
  "trigger": {
    "type": "schema_updated",
    "resource": "users",
    "details": "Schema version 1 → 2"
  },
  "cluster_state": {
    "topics": [ /* all 37 topics with full configs */ ],
    "connectors": [ /* all 37 connectors with status */ ],
    "schemas": [ /* all schemas from registry */ ],
    "consumer_groups": [ /* all consumer groups */ ],
    "metrics_snapshot": { /* recent metrics */ }
  }
}
```

### AgentCore Agent Implementation

Create: `agents/discovery/agent.py`

```python
#!/usr/bin/env python3
"""
Discovery Agent using Amazon Bedrock AgentCore
Event-driven agent that publishes complete cluster snapshots to Kafka
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any
from confluent_kafka import Producer
from bedrock_agentcore import BedrockAgentCoreApp, MCPServerConfig

# Initialize AgentCore Application
app = BedrockAgentCoreApp(
    agent_name="discovery-agent",
    description="Event-driven agent for discovering and inventorying Kafka cluster state",
    model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
    region="us-east-1"
)

# Configure Confluent MCP Server connection
confluent_mcp = MCPServerConfig(
    name="confluent",
    server_type="lambda",
    lambda_function_arn=os.environ["CONFLUENT_MCP_LAMBDA_ARN"],
    environment={
        "CONFLUENT_CLOUD_API_KEY": os.environ["AGENT_CLUSTER_API_KEY"],
        "CONFLUENT_CLOUD_API_SECRET": os.environ["AGENT_CLUSTER_API_SECRET"],
        "CONFLUENT_ENVIRONMENT_ID": os.environ["ENVIRONMENT_ID"],
        "CONFLUENT_KAFKA_CLUSTER_ID": os.environ["CLUSTER_ID"],
        "CONFLUENT_SCHEMA_REGISTRY_ID": os.environ["SCHEMA_REGISTRY_ID"],
        "KAFKA_BOOTSTRAP_ENDPOINT": os.environ["KAFKA_ENDPOINT"],
        "SCHEMA_REGISTRY_ENDPOINT": os.environ["SCHEMA_REGISTRY_ENDPOINT"],
        "SCHEMA_REGISTRY_API_KEY": os.environ["AGENT_SR_API_KEY"],
        "SCHEMA_REGISTRY_API_SECRET": os.environ["AGENT_SR_API_SECRET"]
    }
)

# Register MCP server with agent
app.add_mcp_server(confluent_mcp)

# Configure Kafka Producer
producer_config = {
    'bootstrap.servers': os.environ["KAFKA_ENDPOINT"],
    'security.protocol': 'SASL_SSL',
    'sasl.mechanisms': 'PLAIN',
    'sasl.username': os.environ["AGENT_CLUSTER_API_KEY"],
    'sasl.password': os.environ["AGENT_CLUSTER_API_SECRET"],
    'client.id': 'discovery-agent'
}
producer = Producer(producer_config)

@app.task(name="full-discovery")
async def run_full_discovery(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main task: Perform full discovery and publish complete snapshot to Kafka

    Triggered by cluster events (schema changes, metrics anomalies, etc.)
    Publishes complete cluster state to discovery-events topic
    """

    discovery_timestamp = datetime.utcnow().isoformat()

    # Extract trigger information from event
    trigger_info = event.get('trigger', {
        'type': 'manual',
        'resource': None,
        'details': 'Manual invocation'
    })

    # Task 1: Discover All Topics
    topics_prompt = """
    Using the Confluent MCP server, list all Kafka topics in the cluster.
    For each topic, retrieve:
    1. Partition count and replication factor
    2. Configuration settings (retention.ms, cleanup.policy, etc.)
    3. Associated Avro schema from Schema Registry (if available)
    4. Current message count and throughput metrics

    Return as structured JSON array with all details.
    """

    topics_result = await app.execute_task(
        prompt=topics_prompt,
        tools=["list_topics", "describe_topic", "get_topic_configs", "get_schema"]
    )

    # Task 2: Discover All Connectors
    connectors_prompt = """
    Using the Confluent MCP server, list all connectors.
    For each connector, retrieve:
    1. Connector type (SOURCE/SINK) and class
    2. Status (RUNNING, PAUSED, FAILED) and task details
    3. Full configuration including quickstart template
    4. Associated topic name

    Return as structured JSON array with all details.
    """

    connectors_result = await app.execute_task(
        prompt=connectors_prompt,
        tools=["list_connectors", "describe_connector", "get_connector_config"]
    )

    # Task 3: Discover All Schemas
    schemas_prompt = """
    Using the Confluent MCP server, list all schemas in Schema Registry.
    For each schema subject, retrieve:
    1. Latest schema version and ID
    2. Schema type (AVRO, JSON, PROTOBUF)
    3. Complete schema definition
    4. Subject naming strategy and compatibility mode

    Return as structured JSON array with all details.
    """

    schemas_result = await app.execute_task(
        prompt=schemas_prompt,
        tools=["list_schemas", "get_schema", "describe_schema"]
    )

    # Task 4: Discover Consumer Groups
    consumer_groups_prompt = """
    Using the Confluent MCP server, list all consumer groups.
    For each consumer group, retrieve:
    1. Group ID and state
    2. Members and assigned partitions
    3. Consumer lag per partition
    4. Topics being consumed

    Return as structured JSON array with all details.
    """

    consumer_groups_result = await app.execute_task(
        prompt=consumer_groups_prompt,
        tools=["list_consumer_groups", "describe_consumer_group"]
    )

    # Task 5: Get Metrics Snapshot
    metrics_prompt = """
    Using the Confluent MCP server, get current cluster metrics.
    Retrieve:
    1. Message rates (produce/consume) per topic
    2. Consumer lag metrics
    3. Connector throughput
    4. Cluster health indicators

    Return as structured JSON object with metrics.
    """

    metrics_result = await app.execute_task(
        prompt=metrics_prompt,
        tools=["get_metrics"]
    )

    # Compile complete cluster state snapshot
    cluster_state = {
        "discovery_timestamp": discovery_timestamp,
        "trigger": trigger_info,
        "cluster_state": {
            "environment_id": os.environ["ENVIRONMENT_ID"],
            "cluster_id": os.environ["CLUSTER_ID"],
            "topics": json.loads(topics_result.output),
            "connectors": json.loads(connectors_result.output),
            "schemas": json.loads(schemas_result.output),
            "consumer_groups": json.loads(consumer_groups_result.output),
            "metrics_snapshot": json.loads(metrics_result.output)
        }
    }

    # Publish to Kafka discovery-events topic
    # Key: cluster_id (for log compaction - keeps latest snapshot per cluster)
    # Value: Complete cluster state snapshot
    producer.produce(
        topic='discovery-events',
        key=os.environ["CLUSTER_ID"],
        value=json.dumps(cluster_state),
        callback=delivery_callback
    )
    producer.flush()

    return {
        "statusCode": 200,
        "body": {
            "message": "Discovery complete - snapshot published to Kafka",
            "discovery_timestamp": discovery_timestamp,
            "trigger": trigger_info,
            "topics_discovered": len(cluster_state["cluster_state"]["topics"]),
            "connectors_discovered": len(cluster_state["cluster_state"]["connectors"]),
            "schemas_discovered": len(cluster_state["cluster_state"]["schemas"]),
            "consumer_groups_discovered": len(cluster_state["cluster_state"]["consumer_groups"])
        }
    }


def delivery_callback(err, msg):
    """Kafka producer delivery callback"""
    if err:
        print(f"Failed to deliver message: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")


def lambda_handler(event, context):
    """
    AWS Lambda entry point
    Triggered by various event sources:
    - Schema Registry webhook
    - CloudWatch Alarms (metrics anomalies)
    - EventBridge (new resources, connector failures)
    - Manual API Gateway invocation
    """
    return app.run(task_name="full-discovery", event=event)
```

### AWS Lambda Deployment Configuration

Create: `agents/discovery/serverless.yml` (using Serverless Framework)

```yaml
service: discovery-agent

provider:
  name: aws
  runtime: python3.12
  region: us-east-1
  memorySize: 1024
  timeout: 900  # 15 minutes
  environment:
    # Confluent Cloud configuration
    ENVIRONMENT_ID: ${env:ENVIRONMENT_ID}
    CLUSTER_ID: ${env:CLUSTER_ID}
    KAFKA_ENDPOINT: ${env:KAFKA_ENDPOINT}
    SCHEMA_REGISTRY_ENDPOINT: ${env:SCHEMA_REGISTRY_ENDPOINT}
    SCHEMA_REGISTRY_ID: ${env:SCHEMA_REGISTRY_ID}

    # MCP Server Lambda ARN
    CONFLUENT_MCP_LAMBDA_ARN: !GetAtt ConfluentMCPFunction.Arn

    # Credentials from AWS SSM Parameter Store
    AGENT_CLUSTER_API_KEY: ${ssm:/discovery-agent/cluster-api-key}
    AGENT_CLUSTER_API_SECRET: ${ssm:/discovery-agent/cluster-api-secret}
    AGENT_SR_API_KEY: ${ssm:/discovery-agent/sr-api-key}
    AGENT_SR_API_SECRET: ${ssm:/discovery-agent/sr-api-secret}

  iam:
    role:
      statements:
        # Bedrock access for AgentCore
        - Effect: Allow
          Action:
            - bedrock:InvokeModel
          Resource: arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-*

        # Invoke MCP Server Lambda
        - Effect: Allow
          Action:
            - lambda:InvokeFunction
          Resource: !GetAtt ConfluentMCPFunction.Arn

        # Read credentials from SSM Parameter Store
        - Effect: Allow
          Action:
            - ssm:GetParameter
          Resource: arn:aws:ssm:us-east-1:*:parameter/discovery-agent/*

        # CloudWatch Logs
        - Effect: Allow
          Action:
            - logs:CreateLogGroup
            - logs:CreateLogStream
            - logs:PutLogEvents
          Resource: arn:aws:logs:*:*:*

functions:
  # Main Discovery Agent
  discoveryAgent:
    handler: agent.lambda_handler
    events:
      # Trigger 1: API Gateway for manual invocation
      - http:
          path: discover
          method: post

      # Trigger 2: SNS topic for various events
      - sns:
          arn: !Ref DiscoveryTriggerTopic
          topicName: discovery-agent-triggers

    layers:
      - arn:aws:lambda:us-east-1:123456789012:layer:bedrock-agentcore:1
      - arn:aws:lambda:us-east-1:123456789012:layer:confluent-kafka-python:1

  # Confluent MCP Server as Lambda
  confluentMCP:
    handler: mcp-confluent/build/lambda.handler
    runtime: nodejs22.x
    timeout: 300
    memorySize: 512
    environment:
      CONFLUENT_CLOUD_API_KEY: ${ssm:/discovery-agent/cluster-api-key}
      CONFLUENT_CLOUD_API_SECRET: ${ssm:/discovery-agent/cluster-api-secret}
      CONFLUENT_ENVIRONMENT_ID: ${env:ENVIRONMENT_ID}
      CONFLUENT_KAFKA_CLUSTER_ID: ${env:CLUSTER_ID}
      CONFLUENT_SCHEMA_REGISTRY_ID: ${env:SCHEMA_REGISTRY_ID}
      KAFKA_BOOTSTRAP_ENDPOINT: ${env:KAFKA_ENDPOINT}
      SCHEMA_REGISTRY_ENDPOINT: ${env:SCHEMA_REGISTRY_ENDPOINT}
      SCHEMA_REGISTRY_API_KEY: ${ssm:/discovery-agent/sr-api-key}
      SCHEMA_REGISTRY_API_SECRET: ${ssm:/discovery-agent/sr-api-secret}

  # Schema Registry Change Detector
  schemaChangeDetector:
    handler: triggers/schema_detector.handler
    runtime: python3.12
    timeout: 60
    events:
      # Poll Schema Registry every 5 minutes
      - schedule:
          rate: rate(5 minutes)
          enabled: true
    environment:
      SCHEMA_REGISTRY_ENDPOINT: ${env:SCHEMA_REGISTRY_ENDPOINT}
      SCHEMA_REGISTRY_API_KEY: ${ssm:/discovery-agent/sr-api-key}
      SCHEMA_REGISTRY_API_SECRET: ${ssm:/discovery-agent/sr-api-secret}
      TRIGGER_SNS_TOPIC_ARN: !Ref DiscoveryTriggerTopic

  # Metrics Anomaly Detector
  metricsPoller:
    handler: triggers/metrics_poller.handler
    runtime: python3.12
    timeout: 120
    events:
      # Poll Confluent Metrics API every 5 minutes
      - schedule:
          rate: rate(5 minutes)
          enabled: true
    environment:
      CONFLUENT_CLOUD_API_KEY: ${ssm:/discovery-agent/cluster-api-key}
      CONFLUENT_CLOUD_API_SECRET: ${ssm:/discovery-agent/cluster-api-secret}
      CLUSTER_ID: ${env:CLUSTER_ID}
      TRIGGER_SNS_TOPIC_ARN: !Ref DiscoveryTriggerTopic

  # Connector Status Monitor
  connectorMonitor:
    handler: triggers/connector_monitor.handler
    runtime: python3.12
    timeout: 60
    events:
      # Poll connector status every 3 minutes
      - schedule:
          rate: rate(3 minutes)
          enabled: true
    environment:
      CONFLUENT_MCP_LAMBDA_ARN: !GetAtt ConfluentMCPFunction.Arn
      TRIGGER_SNS_TOPIC_ARN: !Ref DiscoveryTriggerTopic

resources:
  Resources:
    # SNS Topic for triggering discovery agent
    DiscoveryTriggerTopic:
      Type: AWS::SNS::Topic
      Properties:
        TopicName: discovery-agent-triggers
        DisplayName: Discovery Agent Trigger Events
```

### Terraform Integration for Secrets

Add to `terraform/agents.tf`:

```hcl
# Store agent credentials in AWS Systems Manager Parameter Store
resource "aws_ssm_parameter" "discovery_agent_cluster_key" {
  name        = "/discovery-agent/cluster-api-key"
  description = "Discovery Agent Kafka Cluster API Key"
  type        = "SecureString"
  value       = confluent_api_key.discovery_agent_cluster_key.id
}

resource "aws_ssm_parameter" "discovery_agent_cluster_secret" {
  name        = "/discovery-agent/cluster-api-secret"
  description = "Discovery Agent Kafka Cluster API Secret"
  type        = "SecureString"
  value       = confluent_api_key.discovery_agent_cluster_key.secret
}

resource "aws_ssm_parameter" "discovery_agent_sr_key" {
  name        = "/discovery-agent/sr-api-key"
  description = "Discovery Agent Schema Registry API Key"
  type        = "SecureString"
  value       = confluent_api_key.discovery_agent_sr_key.id
}

resource "aws_ssm_parameter" "discovery_agent_sr_secret" {
  name        = "/discovery-agent/sr-api-secret"
  description = "Discovery Agent Schema Registry API Secret"
  type        = "SecureString"
  value       = confluent_api_key.discovery_agent_sr_key.secret
}
```

### Deployment Process

1. **Apply Terraform for Agent Permissions**:
   ```bash
   cd terraform
   terraform apply -target=confluent_service_account.discovery_agent \
                   -target=confluent_api_key.discovery_agent_cluster_key \
                   -target=confluent_api_key.discovery_agent_sr_key \
                   -target=confluent_role_binding.discovery_agent_read_topics \
                   -target=confluent_role_binding.discovery_agent_cluster_admin \
                   -target=aws_ssm_parameter.discovery_agent_cluster_key \
                   -target=aws_ssm_parameter.discovery_agent_cluster_secret \
                   -target=aws_ssm_parameter.discovery_agent_sr_key \
                   -target=aws_ssm_parameter.discovery_agent_sr_secret
   ```

2. **Export Terraform Outputs for Serverless**:
   ```bash
   export ENVIRONMENT_ID=$(terraform output -raw environment_id)
   export CLUSTER_ID=$(terraform output -raw kafka_cluster_id)
   export KAFKA_ENDPOINT=$(terraform output -raw kafka_bootstrap_endpoint)
   export SCHEMA_REGISTRY_ENDPOINT=$(terraform output -raw schema_registry_rest_endpoint)
   export SCHEMA_REGISTRY_ID=$(terraform output -raw schema_registry_id)
   ```

3. **Deploy MCP Server**:
   ```bash
   cd ../agents/discovery

   # Clone and build Confluent MCP
   git clone https://github.com/confluentinc/mcp-confluent.git
   cd mcp-confluent
   npm install
   npm run build

   # Package for Lambda
   npm run package:lambda
   ```

4. **Deploy Agent with Serverless Framework**:
   ```bash
   cd ../agents/discovery

   # Install dependencies
   pip install -r requirements.txt -t ./package
   cp agent.py ./package/

   # Deploy
   serverless deploy
   ```

### Agent Invocation

**Scheduled Execution** (Automatic):
- EventBridge triggers agent every 6 hours
- Results stored in S3: `s3://agentic-data-mesh-discovery-outputs/discovery-outputs/`

**Manual Invocation** (API):
```bash
# Via AWS CLI
aws lambda invoke \
  --function-name discovery-agent-discoveryAgent \
  --payload '{}' \
  response.json

cat response.json

# Via API Gateway
curl -X POST https://abc123.execute-api.us-east-1.amazonaws.com/dev/discover
```

**Programmatic Invocation** (from another agent):
```python
import boto3

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='discovery-agent-discoveryAgent',
    InvocationType='RequestResponse',
    Payload=json.dumps({})
)

result = json.loads(response['Payload'].read())
print(f"Discovery complete: {result['body']['inventory_location']}")
```

### AgentCore Memory Management

The agent uses AgentCore's built-in memory to maintain state:

```python
# Store discovery results for other agents to consume
await app.memory.store("latest_inventory_s3_key", s3_key)
await app.memory.store("latest_inventory_summary", summary)

# Analysis Agent can retrieve this later
inventory_key = await app.memory.retrieve("latest_inventory_s3_key")
s3_data = await app.storage.get_json(bucket=bucket, key=inventory_key)
```

**Memory Backends**:
- DynamoDB (default) - Persistent, shared across invocations
- ElastiCache Redis - High-performance caching
- S3 - Long-term archival

### Cost Estimation

**AWS Lambda**:
- Discovery Agent: ~$0.10 per invocation (15-minute runtime)
- Confluent MCP Lambda: ~$0.02 per invocation (5-minute runtime)
- Scheduled (4x/day): ~$0.50/day

**Amazon Bedrock**:
- Claude Sonnet 3.5: ~$3-5 per 1M tokens
- Estimated per discovery: ~500K tokens = $1.50-2.50
- 4x/day: ~$6-10/day

**Storage**:
- S3: ~$0.023/GB/month (inventories are ~5MB each)
- DynamoDB (memory): ~$0.25/month for low usage

**Total Estimated Cost**: ~$7-12/day for scheduled discovery

## Phase 6: Integration with Analysis Agent

The discovery inventory becomes input for the Analysis Agent:

1. **Entity Relationship Detection**: Analyze schemas to find common fields (user_id, order_id, etc.)
2. **Domain Classification**: Group topics by domain based on connector quickstart templates
3. **Data Quality Profiling**: Sample messages to assess completeness, freshness
4. **Relationship Mapping**: Build lineage graph showing data flow

## Security Considerations

1. **Least Privilege**: Discovery agent only needs READ access (DeveloperRead role)
2. **Credential Storage**:
   - Store in `.env` (gitignored)
   - Or use AWS Secrets Manager / HashiCorp Vault
3. **Audit Trail**: All MCP operations logged via Confluent Cloud audit logs
4. **Network Security**: Ensure MCP server runs in secure network context

## Cost Estimation

- **Discovery Agent Service Account**: Free (no additional cost)
- **API Calls**: Minimal (one-time discovery, ~100-200 REST API calls)
- **Storage**: Negligible (inventory JSON ~ 1-5 MB)

## Next Steps After Discovery

1. **Analyze Inventory**: Run Analysis Agent on discovery outputs
2. **Identify Data Products**: Group topics into logical products
3. **Define Transformations**: Create Flink SQL or ksqlDB for aggregations
4. **Register in Catalog**: Publish data products to data catalog
5. **Iterate**: Re-run discovery periodically to detect new topics/changes

## References

- [Confluent MCP GitHub](https://github.com/confluentinc/mcp-confluent)
- [Confluent Blog: AI Agents with MCP](https://www.confluent.io/blog/ai-agents-using-anthropic-mcp/)
- [Model Context Protocol Spec](https://modelcontextprotocol.io/)
- [Confluent Cloud REST API](https://docs.confluent.io/cloud/current/api.html)
