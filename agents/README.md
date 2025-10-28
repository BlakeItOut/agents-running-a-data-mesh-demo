# Agent Orchestration System

Multi-agent system for transforming raw Kafka data into an organized data mesh, following the architecture defined in `/docs/architecture/agent-flow.md`.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Monitoring Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Deployment  │  │    Usage     │  │   Metrics    │  │
│  │    Agent     │  │    Agent     │  │    Agent     │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
└─────────┼──────────────────┼──────────────────┼──────────┘
          │                  │                  │
          ▼                  ▼                  ▼
  agent-state-       agent-state-       agent-state-
    deployment          usage              metrics
          │                  │                  │
          └──────────┬───────┴────────┬─────────┘
                     ▼                ▼
            ┌──────────────────────────────┐
            │  Current State Agent         │
            │     (Claude Synthesis)       │
            └──────────────┬───────────────┘
                           ▼
                  agent-state-current
                           ▼
                  [ Learning Agent ]
                  [ Evaluation Agents ]
                  [ ... ]
```

## Quick Start

### Option A: Dry-Run Mode (Fastest - No Infrastructure Needed)

Perfect for testing without deploying any infrastructure:

```bash
cd agents

# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install Python dependencies (includes anthropic, confluent-kafka, etc.)
pip install -r requirements.txt

# 3. Set your Anthropic API key (only requirement for dry-run)
export ANTHROPIC_API_KEY="sk-ant-api03-your-key-here"

# 4. Run the bootstrap in dry-run mode
python bootstrap.py --dry-run
```

**What happens:** All 4 agents run and save output to `dry-run-output/` directory. Claude synthesizes the state.

### Option B: Full Mode (With Kafka Infrastructure)

Requires deployed Confluent Cloud infrastructure:

#### 1. Prerequisites

- Python 3.10+ installed
- Node.js installed (for MCP server via npx)
- Terraform infrastructure deployed (37 Kafka topics)
- Confluent Cloud credentials
- Anthropic API key

#### 2. Setup Environment

```bash
cd agents

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (anthropic, confluent-kafka, mcp, boto3, python-dotenv)
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

#### 3. Configure Environment Variables

Your `.env` file needs:

```bash
# Kafka Cluster
KAFKA_BOOTSTRAP_ENDPOINT=pkc-xxxxx.us-east-1.aws.confluent.cloud:9092
KAFKA_API_KEY=YOUR_CLUSTER_API_KEY
KAFKA_API_SECRET=YOUR_CLUSTER_API_SECRET

# Schema Registry
SCHEMA_REGISTRY_URL=https://psrc-xxxxx.us-east-2.aws.confluent.cloud
SCHEMA_REGISTRY_API_KEY=YOUR_SR_API_KEY
SCHEMA_REGISTRY_API_SECRET=YOUR_SR_API_SECRET

# Confluent Cloud (for MCP - org-level)
CONFLUENT_CLOUD_API_KEY=YOUR_CLOUD_API_KEY
CONFLUENT_CLOUD_API_SECRET=YOUR_CLOUD_API_SECRET

# Claude API
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
```

**Get credentials from Terraform:**
```bash
cd ../terraform
terraform output -json | jq -r '
  "KAFKA_BOOTSTRAP_ENDPOINT=\(.kafka_bootstrap_endpoint.value)\n" +
  "KAFKA_API_KEY=\(.cluster_admin_api_key.value)\n" +
  "KAFKA_API_SECRET=\(.cluster_admin_api_secret.value)\n" +
  "SCHEMA_REGISTRY_URL=\(.schema_registry_rest_endpoint.value)\n" +
  "SCHEMA_REGISTRY_API_KEY=\(.schema_registry_api_key.value)\n" +
  "SCHEMA_REGISTRY_API_SECRET=\(.schema_registry_api_secret.value)"
'
```

#### 4. Deploy Infrastructure

Before running agents, deploy the agent topics and schemas:

```bash
cd ../terraform
terraform apply
```

This creates:
- 4 Kafka topics: `agent-state-deployment`, `agent-state-usage`, `agent-state-metrics`, `agent-state-current`
- Avro schemas registered in Schema Registry
- Proper RBAC permissions

#### 5. Run Bootstrap

```bash
cd agents
source venv/bin/activate
python bootstrap.py
```

**What bootstrap.py does:**
1. Runs Deployment Agent → discovers 37 topics from Confluent Cloud
2. Runs Usage Agent → generates synthetic usage data
3. Runs Metrics Agent → generates synthetic metrics
4. Runs Current State → synthesizes with Claude
5. Publishes aggregated state to `agent-state-current`

**Expected output:**
```
==================================================================
           AGENT ORCHESTRATION BOOTSTRAP
==================================================================

STEP 1: Deployment Agent
  Found 37 topics
  Found 37 schemas
  Found 37 connectors
  ✅ Deployment state published successfully!

STEP 2: Usage Agent
  ✅ Usage state published successfully!

STEP 3: Metrics Agent
  ✅ Metrics state published successfully!

STEP 4: Current State Agent
  ✅ Current state published successfully!

==================================================================
                    BOOTSTRAP COMPLETE!
==================================================================

💡 Claude's Summary:
  The platform has 37 active data streams across 12 domains with no
  consumers yet. Infrastructure is healthy with low latency and no errors.

✅ All agent state topics are now populated!
```

## Directory Structure

```
agents/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── .env                        # Environment variables (gitignored)
├── .env.example                # Environment template
├── bootstrap.py                # Main orchestration script
├── schemas/                    # Avro schemas
│   ├── deployment-state.avsc
│   ├── usage-state.avsc
│   ├── metrics-state.avsc
│   └── current-state.avsc
├── common/                     # Shared utilities
│   ├── kafka_utils.py         # Kafka producers/consumers
│   ├── claude_utils.py        # Claude API wrapper
│   └── schema_utils.py        # Schema loading
├── monitoring/                 # Monitoring layer agents
│   ├── deployment.py          # Discovers Confluent state via MCP
│   ├── usage.py               # Usage metrics (synthetic for now)
│   └── metrics.py             # System metrics (synthetic for now)
└── ideation/                   # Ideation layer agents
    └── current-state.py       # Synthesizes 3 states with Claude
```

## Individual Agents

### Run agents individually for testing:

```bash
# Deployment Agent (requires MCP server)
python monitoring/deployment.py

# Usage Agent (synthetic)
python monitoring/usage.py

# Metrics Agent (synthetic)
python monitoring/metrics.py

# Current State (requires all 3 above to have run)
python ideation/current-state.py
```

## Verification

Check that messages were published:

```bash
# View latest deployment state
kafka-console-consumer \
  --bootstrap-server $KAFKA_BOOTSTRAP_ENDPOINT \
  --topic agent-state-deployment \
  --from-beginning \
  --max-messages 1 \
  --consumer.config client.properties

# View current state (Claude synthesis)
kafka-console-consumer \
  --bootstrap-server $KAFKA_BOOTSTRAP_ENDPOINT \
  --topic agent-state-current \
  --from-beginning \
  --max-messages 1 \
  --consumer.config client.properties
```

## Next Steps

After bootstrap completes, the `agent-state-current` topic contains the synthesized platform state. This becomes the input for the **Learning Agent** (not yet implemented), which will:

1. Read from `agent-state-current`
2. Generate ideas for data products
3. Publish to `agent-state-raw-ideas`
4. Continue through the agent-flow.md architecture

## Troubleshooting

### "anthropic package not installed" Error

If you see: `⚠️ Claude synthesis failed: anthropic package not installed`

**Solution:**
```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt

# Or install anthropic specifically
pip install anthropic
```

**Verify installation:**
```bash
python -c "import anthropic; print('anthropic installed:', anthropic.__version__)"
```

### Missing ANTHROPIC_API_KEY

If Claude synthesis fails with missing API key:

**Solution:**
```bash
# Set in your environment
export ANTHROPIC_API_KEY="sk-ant-api03-your-key-here"

# Or add to .env file
echo "ANTHROPIC_API_KEY=sk-ant-api03-your-key-here" >> .env
```

Get your API key from: https://console.anthropic.com/settings/keys

### MCP Connection Fails
- Ensure `npx` is available: `npx --version`
- Check Confluent Cloud credentials in `.env`
- Verify `.env` file path in deployment.py
- Only required for full mode (not dry-run)

### Kafka Publishing Fails
- Verify cluster API key has write permissions
- Check Schema Registry credentials
- Ensure topics exist: `terraform output agent_topic_names`
- Try dry-run mode to test without Kafka: `python bootstrap.py --dry-run`

### Claude API Fails
- Check `ANTHROPIC_API_KEY` is valid
- Verify API quota/billing at https://console.anthropic.com/
- Fallback synthesis will be used if Claude fails (basic summary)

## Cost Considerations

- **Kafka Topics**: 4 topics with log compaction (minimal cost)
- **Confluent Cloud**: Existing cluster cost (~$9-10/hour)
- **Claude API**: ~$0.01-0.05 per bootstrap run
- **Total**: < $0.10 per bootstrap execution

## Development

To add new agents:

1. Create agent file in appropriate layer directory
2. Import common utilities from `common/`
3. Follow pattern: read from Kafka → process → write to Kafka
4. Add to `bootstrap.py` if part of main flow

## References

- Architecture: `/docs/architecture/agent-flow.md`
- Terraform: `/terraform/`
- Discovery Agent Prototype: `/agents/discovery/` (on feat/discovery-agent branch)
