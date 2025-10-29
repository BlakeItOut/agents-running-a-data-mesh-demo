# Agents Running a Data Mesh

**Autonomous agents transforming raw, stream-based data into a product-oriented, discoverable data mesh**

This repository demonstrates how AI agents can analyze, organize, and structure streaming data into well-defined, reusable data products. The system creates a realistic "raw data mess" in Confluent Cloud and uses autonomous agents to transform it into a governed, discoverable data mesh.

## What's Inside

- **37 Streaming Data Sources** across 12 domains (financial, e-commerce, gaming, fleet management, IoT, and more)
- **Autonomous Agent Pipeline** that discovers, analyzes, refines, evaluates, and implements data products
- **Complete Infrastructure** provisioned via Terraform (Kafka clusters, Schema Registry, RBAC, connectors)
- **Human-in-the-Loop Workflows** for refinement and approval at key decision points
- **Production-Ready Implementations** with Terraform configurations, ksqlDB/Flink SQL queries, and documentation

## Quick Start

### 1. Set Up Infrastructure

```bash
# Set up Confluent Cloud credentials
cp .env.example .env
# Edit .env with your Cloud API keys

# Deploy infrastructure (~15-20 minutes)
cd terraform
terraform init
terraform apply
```

See [Terraform Setup Guide](docs/setup/TERRAFORM_GUIDE.md) for detailed instructions.

### 2. Run the Agent Pipeline

```bash
# Set up agent environment
cd agents
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Configure agent credentials (from terraform outputs)
cp .env.example .env
# Edit agents/.env with Kafka and Claude API credentials

# Run the full pipeline
./venv/bin/python3 bootstrap.py
```

See [Agent Getting Started Guide](docs/agents/GETTING_STARTED.md) for detailed instructions.

### 3. Test in Dry-Run Mode

```bash
# Test without using Claude API or connecting to Kafka
./venv/bin/python3 bootstrap.py --dry-run
```

## Architecture

The system uses a multi-phase agent pipeline:

```
Raw Data (37 Topics)
  → Discovery Agent (finds patterns, domains)
  → Analysis Agent (proposes data products)
  → Refinement Agent (human-in-the-loop editing)
  → Evaluation Agents (scope/time/cost analysis)
  → Implementation Agent (generates Terraform, SQL, docs)
  → Monitoring (planned)
```

See [Architecture Documentation](docs/agents/ARCHITECTURE.md) for detailed flow diagrams.

## Documentation

### Getting Started
- [Terraform Setup Guide](docs/setup/TERRAFORM_GUIDE.md) - Deploy Confluent Cloud infrastructure
- [Environment Configuration](docs/setup/ENVIRONMENT_CONFIG.md) - Configure credentials and API keys
- [Agent Getting Started](docs/agents/GETTING_STARTED.md) - Run the agent pipeline

### Workflows
- [Human Refinement Workflow](docs/workflows/HUMAN_REFINEMENT.md) - Interactive refinement process
- [Evaluation Phase](docs/workflows/EVALUATION_PHASE.md) - "Shark Tank" evaluation layer

### Project Information
- [Vision and Status](docs/project/VISION_AND_STATUS.md) - Complete project vision and current progress
- [Architecture](docs/agents/ARCHITECTURE.md) - Technical architecture and flow diagrams

### Historical
- [Initial Specification](docs/historical/INITIAL_SPEC.md) - Original project spec

## Key Features

### Realistic Data Environment
- 37 different Kafka topics using Confluent datagen connectors
- 12 domains: financial, e-commerce, gaming, fleet management, IoT, insurance, HR, security, and more
- Continuous data generation (configurable message rates)
- Full Schema Registry integration with Avro schemas

### Autonomous Agent Pipeline
- **Discovery**: Analyzes raw topics to find domains and patterns
- **Analysis**: Proposes valuable data products with clear use cases
- **Refinement**: Human-in-the-loop editing and approval
- **Evaluation**: Multi-agent "Shark Tank" analyzing scope, time, and cost
- **Implementation**: Generates production-ready Terraform, SQL, and documentation

### Production-Ready Outputs
- Terraform configurations for Kafka topics, schemas, and ACLs
- ksqlDB/Flink SQL queries for data transformations
- Complete documentation with architecture diagrams
- Git branches and pull requests for review

## Cost Considerations

- **Confluent Cloud**: Standard cluster costs ~$9-10/hour ($220-240/day if left running)
- **Claude API**: Varies by usage (Haiku for agents, Sonnet for complex tasks)
- **Recommendation**: Use terraform destroy when not actively demoing

See [Terraform Setup Guide](docs/setup/TERRAFORM_GUIDE.md) for cost optimization strategies.

## Requirements

- **Confluent Cloud Account** with payment method configured
- **Confluent Cloud API Keys** (organization-level, not cluster-specific)
- **Claude API Key** (Anthropic) or AWS Bedrock access
- **Terraform** >= 1.0
- **Python** 3.8+
- **gh CLI** (for PR creation)

## Contributing

This is a demonstration project showcasing agent-driven data mesh transformation. Contributions, feedback, and improvements are welcome!

## License

[MIT License](LICENSE) (or specify your license)

## Learn More

- [Complete Documentation Hub](docs/README.md)
- [Project Vision and Roadmap](docs/project/VISION_AND_STATUS.md)
- [Architecture Deep Dive](docs/agents/ARCHITECTURE.md)
