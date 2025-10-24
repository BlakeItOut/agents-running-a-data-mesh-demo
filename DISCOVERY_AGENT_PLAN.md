# Discovery Agent - COMPLETED ✅

## Status Summary

**Phases 1-4**: ✅ COMPLETED and operational
**Phases 5-6**: 📋 Future work (AWS Lambda/Bedrock deployment)

### What's Working

- ✅ **37 Kafka topics** discovered with full metadata
- ✅ **37 Avro schemas** retrieved with complete field definitions
- ✅ **37 datagen connectors** inventoried
- ✅ **9 data product candidates** identified through domain analysis
- ✅ **6 improvement recommendations** generated automatically

---

## Quick Start Guide

### Prerequisites

- Python 3.10+ installed (we're using 3.14)
- Node.js for MCP server (uses npx)
- Terraform outputs configured
- Confluent Cloud credentials in root `.env`

### Running Discovery

1. **Navigate to discovery agent directory**:
   ```bash
   cd agents/discovery
   ```

2. **Activate Python virtual environment**:
   ```bash
   source venv/bin/activate
   ```

3. **Run discovery** (inventories all resources):
   ```bash
   python run-discovery.py
   ```

   **Output**:
   ```
   Connecting to Confluent MCP server...
   Connected!
   Discovering topics...
   Found 37 topics
   Discovering schemas...
   Found 37 schema subjects
   Discovering connectors...
   Found 37 connectors

   Discovery complete! Inventory saved to discovery-outputs/inventory-[timestamp].json
   ```

4. **Analyze inventory** (generate data product suggestions):
   ```bash
   python analyze-inventory.py
   ```

   **Output**: Data product recommendations and improvement suggestions

### Output Files

All outputs saved to `agents/discovery/discovery-outputs/`:
- `inventory-[timestamp].json` - Complete cluster inventory (topics, schemas, connectors)
- `analysis-[timestamp].json` - Data product suggestions and improvements

---

## Architecture (Implemented)

```
┌─────────────────────────────────────────────────┐
│   Python Discovery Scripts                      │
│   - run-discovery.py (inventory)                │
│   - analyze-inventory.py (analysis)             │
└────────────────┬────────────────────────────────┘
                 │ MCP Python SDK (async/await)
┌────────────────▼────────────────────────────────┐
│   Confluent MCP Server                          │
│   (npx @confluentinc/mcp-confluent)             │
│                                                 │
│   Tools Used:                                   │
│   - list-topics                                 │
│   - list-schemas                                │
│   - list-connectors                             │
└────────────────┬────────────────────────────────┘
                 │ Confluent Cloud REST API
┌────────────────▼────────────────────────────────┐
│   Confluent Cloud                               │
│   Environment: agentic-data-mesh (env-7zpqx1)   │
│   Cluster: data-mesh-cluster (lkc-nd1ng3)       │
│                                                 │
│   Resources:                                    │
│   - 37 Kafka Topics with Avro schemas          │
│   - 37 Datagen Source Connectors               │
│   - Schema Registry (ESSENTIALS)               │
└─────────────────────────────────────────────────┘
```

---

## Implementation Details

### Phase 1: Terraform Resources ✅

**Location**: `terraform/agents.tf`

**Created Resources**:
1. `confluent_service_account.discovery_agent`
2. `confluent_api_key.discovery_agent_cloud_key` - **Cloud API Key** (org-level)
3. `confluent_api_key.discovery_agent_cluster_key` - Cluster API Key
4. `confluent_api_key.discovery_agent_sr_key` - Schema Registry API Key
5. `confluent_role_binding.discovery_agent_read_topics` - DeveloperRead
6. `confluent_role_binding.discovery_agent_cluster_admin` - CloudClusterAdmin
7. `confluent_role_binding.discovery_agent_env_admin` - EnvironmentAdmin

**Key Insight**: Two API key types required:
- **Cloud API Key** (no `managed_resource`) → org-level access
- **Cluster API Key** (with `managed_resource`) → cluster-specific operations

### Phase 2: MCP Configuration ✅

**Location**: `agents/discovery/`

**Files**:
- `configure-mcp.sh` - Populates `.env` from Terraform outputs
- `.env` - MCP server credentials (gitignored)
- `mcp-config.json` - MCP server configuration

**Environment Variables** (auto-populated by `configure-mcp.sh`):
```bash
# Cloud API (org-level)
CONFLUENT_CLOUD_API_KEY=JWVWHPCNLIJ55ZCK
CONFLUENT_CLOUD_API_SECRET=...

# Cluster API (cluster-specific)
KAFKA_API_KEY=D56WQWTXWOPIFPCY
KAFKA_API_SECRET=...
BOOTSTRAP_SERVERS=pkc-oxqxx9.us-east-1.aws.confluent.cloud:9092

# Schema Registry
SCHEMA_REGISTRY_API_KEY=AF53WSL4STBJ32LG
SCHEMA_REGISTRY_API_SECRET=...
```

**Regenerate credentials**:
```bash
cd agents/discovery
source ../../.env  # Load Terraform Cloud API key
./configure-mcp.sh
```

### Phase 3: Discovery Script ✅

**Location**: `agents/discovery/run-discovery.py`

**Implementation**: Python MCP SDK with async/await

**Key Functions**:
- `init_mcp_client()` - Connect to Confluent MCP server via stdio
- `run_mcp_command(session, tool_name, params)` - Execute MCP tools
- `discover_topics(session)` - Parse comma-separated topic list
- `discover_schemas(session)` - Parse JSON schema dictionary
- `discover_connectors(session)` - Parse connector list

**Output Format** (`discovery-outputs/inventory-[timestamp].json`):
```json
{
  "environment": "agentic-data-mesh",
  "cluster": "data-mesh-cluster",
  "discovery_timestamp": "2025-10-24T06:44:14.106567+00:00",
  "topics": [
    {"name": "fleet_mgmt_sensors"},
    {"name": "gaming_player_activity"},
    ...
  ],
  "schemas": [
    {
      "subject": "fleet_mgmt_sensors-value",
      "versions": [
        {
          "version": 1,
          "id": 100037,
          "schema": "{\"type\":\"record\",\"name\":\"fleet_mgmt_sensors\"...}"
        }
      ]
    },
    ...
  ],
  "connectors": [
    {"name": "datagen-fleet_mgmt_sensors"},
    {"name": "datagen-gaming_player_activity"},
    ...
  ]
}
```

### Phase 4: Analysis Script ✅

**Location**: `agents/discovery/analyze-inventory.py`

**Capabilities**:
1. **Domain Detection** - Groups topics by schema namespace (12 domains found)
2. **Data Product Suggestions** - Identifies 9 multi-topic data products
3. **Quality Assessment** - Detects naming inconsistencies, namespace issues
4. **Improvement Recommendations** - Prioritized list of enhancements

**Discovered Domains**:
- `clickstream` (3 topics)
- `fleet_mgmt` (3 topics)
- `gaming` (3 topics)
- `insurance` (3 topics)
- `pizza_orders` (3 topics)
- `shoes` (4 topics)
- `payroll` (3 topics)
- `ksql` (7 topics)
- `datagen` (5 topics)
- Plus 3 single-topic domains

**Suggested Data Products**:
1. **clickstream-data-product** - Web analytics (clickstream, clickstream_codes, clickstream_users)
2. **fleet-mgmt-data-product** - Vehicle tracking (location, sensors, descriptions)
3. **gaming-data-product** - Gaming platform (games, players, activity)
4. **insurance-data-product** - Customer management (customers, offers, activity)
5. **pizza-orders-data-product** - Order lifecycle (orders, cancelled, completed)
6. **shoes-data-product** - E-commerce (products, customers, orders, clickstream)
7. **payroll-data-product** - HR payroll (employees, location, bonuses)
8. **ksql-data-product** - Business operations (inventory, orders, stock trades, ratings)
9. **datagen-data-product** - Financial data (credit cards, transactions, stores)

**Recommended Improvements**:
1. [High] Fix 5 topics using generic `datagen.example` namespace
2. [High] Add business metadata (tags, descriptions, owners, SLAs)
3. [Medium] Define schema evolution strategy (all schemas are v1)
4. [Low] Review 3 single-topic domains for consolidation

---

## Directory Structure

```
agents/discovery/
├── run-discovery.py           # Main discovery script (Python MCP SDK)
├── analyze-inventory.py       # Analysis and recommendations
├── configure-mcp.sh           # Populates .env from Terraform outputs
├── mcp-config.json           # MCP server configuration
├── .env                      # Credentials (gitignored)
├── venv/                     # Python virtual environment (gitignored)
└── discovery-outputs/        # Inventory and analysis JSON (gitignored)
    ├── inventory-[timestamp].json
    └── analysis-[timestamp].json
```

---

## Maintenance

### Updating Credentials

If Terraform resources are recreated:

```bash
cd agents/discovery
source ../../.env
./configure-mcp.sh
```

### Adding Python Dependencies

```bash
cd agents/discovery
source venv/bin/activate
pip install <package>
pip freeze > requirements.txt  # If you want to track dependencies
```

### Re-running Discovery

Discovery can be run as often as needed to track changes:

```bash
cd agents/discovery
source venv/bin/activate
python run-discovery.py
python analyze-inventory.py
```

---

# FUTURE WORK (Phases 5-6)

## Phase 5: Production Deployment with Claude Agents SDK (Not Implemented)

**Goal**: Deploy discovery agent as event-driven service using **Claude Agents SDK** with AWS Lambda for infrastructure.

**Why Claude Agents SDK over AWS Bedrock AgentCore**:
- ✅ **Cloud Agnostic** - Runs anywhere (AWS, GCP, Docker, local)
- ✅ **Simpler** - Direct Python SDK, less infrastructure complexity
- ✅ **Portable** - Easy to migrate between clouds or run hybrid
- ✅ **Test Locally** - Run the same code on your laptop
- ✅ **Latest Features** - Anthropic SDK gets Claude updates first

**Architecture**:
```
┌─────────────────────────────────────────────────────────┐
│   Event Triggers (AWS)                                   │
│   - EventBridge Schedule (every 6 hours)                │
│   - SNS Topics (schema changes, metrics anomalies)      │
│   - API Gateway (manual invocation)                     │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│   AWS Lambda (thin wrapper)                             │
│   - Parse event triggers                                │
│   - Load secrets from SSM                               │
│   - Invoke agent                                        │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│   Discovery Agent (Claude Agents SDK - portable)        │
│   ┌─────────────────────────────────────────────────┐   │
│   │  discovery_agent.py                             │   │
│   │  - Anthropic SDK for Claude API                 │   │
│   │  - MCP Python SDK for Confluent MCP             │   │
│   │  - Agent orchestration logic                    │   │
│   │  - Kafka producer (confluent-kafka-python)      │   │
│   └──────────────┬──────────────────────────────────┘   │
└─────────────────┼────────────────────────────────────────┘
                  │ MCP              │ Kafka
       ┌──────────▼──────┐    ┌──────▼──────────────────┐
       │ Confluent MCP   │    │  discovery-events       │
       │ (npx via stdio) │    │  (log compacted topic)  │
       └─────────────────┘    └─────────────────────────┘
```

**Key Features**:
- **Cloud-agnostic core** - Agent logic runs anywhere
- **AWS for infrastructure** - Lambda, EventBridge, IAM, SSM
- **Event-driven execution** - Schema changes, metrics anomalies, schedule
- **Event-carried state** - Complete cluster snapshots published to Kafka
- **Testable locally** - Run discovery_agent.py directly

**Components to Build**:
1. `discovery_agent.py` - Claude Agents SDK implementation (portable)
2. `lambda_handler.py` - Thin AWS wrapper (AWS-specific)
3. `serverless.yml` - AWS deployment config
4. Trigger functions (schema detector, metrics poller)
5. Terraform for AWS SSM Parameter Store

**Event-Carried State Pattern**:
Each message in `discovery-events` topic contains complete cluster state:
```json
{
  "discovery_timestamp": "2025-10-24T10:15:00Z",
  "trigger": {
    "type": "schema_updated",
    "resource": "users",
    "details": "Schema version 1 → 2"
  },
  "cluster_state": {
    "topics": [ /* all 37 topics with configs */ ],
    "connectors": [ /* all 37 connectors with status */ ],
    "schemas": [ /* all schemas */ ],
    "consumer_groups": [ /* all groups */ ],
    "metrics_snapshot": { /* recent metrics */ }
  }
}
```

**Benefits**:
- Consumers get everything in one message (no joins, no lookups)
- Topic compaction keeps only latest snapshot per cluster
- 200K token context windows can easily handle 37 topics + schemas

### Implementation Example

**1. Cloud-Agnostic Agent** (`discovery_agent.py`):
```python
#!/usr/bin/env python3
"""
Discovery Agent using Claude Agents SDK
Portable - runs anywhere (AWS Lambda, GCP, Docker, local)
"""
import asyncio
import json
from datetime import datetime, UTC
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from confluent_kafka import Producer

class DiscoveryAgent:
    """Cloud-agnostic discovery agent using Claude Agents SDK"""

    def __init__(self, anthropic_api_key, confluent_config):
        self.anthropic = Anthropic(api_key=anthropic_api_key)
        self.confluent_config = confluent_config
        self.producer = Producer({
            'bootstrap.servers': confluent_config['bootstrap_servers'],
            'security.protocol': 'SASL_SSL',
            'sasl.mechanisms': 'PLAIN',
            'sasl.username': confluent_config['kafka_api_key'],
            'sasl.password': confluent_config['kafka_api_secret']
        })

    async def run_discovery(self, trigger_info=None):
        """
        Main discovery workflow
        Works identically on Lambda, GCP, Docker, or local machine
        """
        timestamp = datetime.now(UTC).isoformat()

        # Connect to Confluent MCP server
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@confluentinc/mcp-confluent", "-e", ".env"],
            env=None
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as mcp_session:
                await mcp_session.initialize()

                # List available MCP tools
                tools = await mcp_session.list_tools()

                # Use Claude to orchestrate discovery
                discovery_prompt = f"""
                You are a discovery agent analyzing a Confluent Cloud cluster.

                Trigger: {trigger_info or 'Scheduled discovery'}
                Timestamp: {timestamp}

                Tasks:
                1. List all Kafka topics using list-topics tool
                2. Get all schemas from Schema Registry using list-schemas tool
                3. List all connectors using list-connectors tool
                4. Return results as structured JSON

                Focus on gathering complete inventory data.
                """

                # Call Claude with MCP tools
                response = await self.anthropic.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=8192,
                    tools=[{
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema
                    } for tool in tools.tools],
                    messages=[{
                        "role": "user",
                        "content": discovery_prompt
                    }]
                )

                # Process tool calls from Claude
                results = await self._execute_tool_calls(mcp_session, response)

                # Build cluster snapshot
                cluster_state = {
                    "discovery_timestamp": timestamp,
                    "trigger": trigger_info or {"type": "scheduled"},
                    "cluster_state": results
                }

                # Publish to Kafka
                self.producer.produce(
                    topic='discovery-events',
                    key=self.confluent_config['cluster_id'],
                    value=json.dumps(cluster_state)
                )
                self.producer.flush()

                return cluster_state

    async def _execute_tool_calls(self, mcp_session, claude_response):
        """Execute MCP tools based on Claude's decisions"""
        results = {}

        for content in claude_response.content:
            if content.type == "tool_use":
                tool_result = await mcp_session.call_tool(
                    content.name,
                    arguments=content.input
                )
                results[content.name] = tool_result

        return results

# Can run locally for testing
if __name__ == "__main__":
    import os
    agent = DiscoveryAgent(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        confluent_config={
            'bootstrap_servers': os.getenv("BOOTSTRAP_SERVERS"),
            'kafka_api_key': os.getenv("KAFKA_API_KEY"),
            'kafka_api_secret': os.getenv("KAFKA_API_SECRET"),
            'cluster_id': os.getenv("KAFKA_CLUSTER_ID")
        }
    )
    asyncio.run(agent.run_discovery())
```

**2. AWS Lambda Wrapper** (`lambda_handler.py`):
```python
"""
Thin AWS wrapper - only AWS-specific code here
Agent logic remains portable in discovery_agent.py
"""
import json
import asyncio
import boto3
from discovery_agent import DiscoveryAgent

# AWS clients
ssm = boto3.client('ssm')

def get_secrets_from_ssm():
    """Load secrets from AWS SSM Parameter Store"""
    return {
        'anthropic_api_key': ssm.get_parameter(
            Name='/discovery-agent/anthropic-api-key',
            WithDecryption=True
        )['Parameter']['Value'],
        'bootstrap_servers': ssm.get_parameter(
            Name='/discovery-agent/bootstrap-servers'
        )['Parameter']['Value'],
        'kafka_api_key': ssm.get_parameter(
            Name='/discovery-agent/kafka-api-key',
            WithDecryption=True
        )['Parameter']['Value'],
        'kafka_api_secret': ssm.get_parameter(
            Name='/discovery-agent/kafka-api-secret',
            WithDecryption=True
        )['Parameter']['Value'],
        'cluster_id': ssm.get_parameter(
            Name='/discovery-agent/cluster-id'
        )['Parameter']['Value']
    }

def lambda_handler(event, context):
    """AWS Lambda entry point - thin wrapper"""

    # Parse trigger from AWS event
    trigger_info = {
        'type': event.get('source', 'manual'),
        'resource': event.get('detail', {}).get('resource'),
        'details': json.dumps(event.get('detail', {}))
    }

    # Load secrets
    secrets = get_secrets_from_ssm()

    # Create agent (portable)
    agent = DiscoveryAgent(
        anthropic_api_key=secrets['anthropic_api_key'],
        confluent_config={
            'bootstrap_servers': secrets['bootstrap_servers'],
            'kafka_api_key': secrets['kafka_api_key'],
            'kafka_api_secret': secrets['kafka_api_secret'],
            'cluster_id': secrets['cluster_id']
        }
    )

    # Run discovery (same code works locally or in Lambda)
    result = asyncio.run(agent.run_discovery(trigger_info))

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Discovery complete',
            'timestamp': result['discovery_timestamp'],
            'topics_count': len(result['cluster_state'].get('topics', [])),
            'schemas_count': len(result['cluster_state'].get('schemas', []))
        })
    }
```

**3. Serverless Framework Config** (`serverless.yml`):
```yaml
service: discovery-agent

provider:
  name: aws
  runtime: python3.12
  region: us-east-1
  memorySize: 1024
  timeout: 300  # 5 minutes
  iam:
    role:
      statements:
        # Anthropic API via Bedrock or direct
        - Effect: Allow
          Action: bedrock:InvokeModel
          Resource: 'arn:aws:bedrock:*::foundation-model/anthropic.claude-*'
        # Read secrets
        - Effect: Allow
          Action: ssm:GetParameter
          Resource: 'arn:aws:ssm:*:*:parameter/discovery-agent/*'

functions:
  discover:
    handler: lambda_handler.lambda_handler
    events:
      # Scheduled every 6 hours
      - schedule:
          rate: rate(6 hours)
          enabled: true

      # Manual API trigger
      - http:
          path: discover
          method: post

      # SNS trigger for schema changes
      - sns:
          arn: !Ref DiscoveryTriggerTopic
          topicName: discovery-agent-triggers

    layers:
      - arn:aws:lambda:us-east-1:123456789012:layer:anthropic-sdk:1
      - arn:aws:lambda:us-east-1:123456789012:layer:mcp-python-sdk:1
      - arn:aws:lambda:us-east-1:123456789012:layer:confluent-kafka:1

resources:
  Resources:
    DiscoveryTriggerTopic:
      Type: AWS::SNS::Topic
      Properties:
        TopicName: discovery-agent-triggers
```

**4. Local Testing** (no AWS needed):
```bash
# Test locally with same code
cd agents/discovery
source venv/bin/activate

# Set environment variables
export ANTHROPIC_API_KEY="sk-..."
export BOOTSTRAP_SERVERS="pkc-..."
export KAFKA_API_KEY="..."
export KAFKA_API_SECRET="..."
export KAFKA_CLUSTER_ID="lkc-..."

# Run agent locally
python discovery_agent.py
```

**5. Deploy to AWS**:
```bash
serverless deploy
```

**6. Or Deploy to GCP Cloud Run** (same agent code!):
```bash
gcloud run deploy discovery-agent \
  --source . \
  --region us-central1
```

### Estimated Cost (4x/day scheduled)

- **Lambda Compute**: ~$0.10/day (5-min runtime)
- **Claude API** (direct to Anthropic): ~$3-5/day
  - Or via AWS Bedrock: ~$4-7/day (slight markup)
- **AWS Services** (EventBridge, SSM): <$0.10/day
- **Kafka Producer**: Negligible

**Total**: ~$3-8/day depending on Claude pricing tier

*Much simpler and cheaper than AgentCore approach!*

## Phase 6: Integration with Analysis Agent (Not Implemented)

**Goal**: Consume discovery events to power downstream analysis.

**Use Cases**:
1. **Entity Relationship Detection** - Find common fields (user_id, order_id)
2. **Domain Classification** - Automated domain grouping
3. **Data Quality Profiling** - Sample messages, assess completeness
4. **Lineage Mapping** - Build data flow graphs

**Implementation**:
- Analysis Agent subscribes to `discovery-events` topic
- Uses latest cluster snapshot as context
- Applies ML/LLM for pattern detection
- Publishes analysis results to `analysis-events` topic

---

## Security Considerations

1. **Least Privilege**: Discovery agent has READ-only access (DeveloperRead)
2. **Credential Management**:
   - Terraform stores credentials as sensitive outputs
   - `.env` file gitignored
   - AWS SSM Parameter Store for Lambda deployment
3. **Audit Trail**: All operations logged via Confluent Cloud audit logs
4. **RBAC**: Uses proper roles (not ACLs) for permission management

---

## References

- [Confluent MCP GitHub](https://github.com/confluentinc/mcp-confluent)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Anthropic SDK (Python)](https://github.com/anthropics/anthropic-sdk-python)
- [Claude API Documentation](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)
- [Confluent Cloud REST API](https://docs.confluent.io/cloud/current/api.html)
- [AWS Lambda Python](https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html)
- [Serverless Framework](https://www.serverless.com/framework/docs)
