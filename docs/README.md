# Documentation Hub

Welcome to the Agents Running a Data Mesh documentation! This guide will help you navigate the documentation based on your role and needs.

## Quick Links by Role

### 🆕 First-Time Users
1. [Terraform Setup Guide](setup/TERRAFORM_GUIDE.md) - Deploy Confluent Cloud infrastructure
2. [Environment Configuration](setup/ENVIRONMENT_CONFIG.md) - Configure credentials and API keys
3. [Agent Getting Started](agents/GETTING_STARTED.md) - Run the agent pipeline

### 👨‍💻 Developers
- [Agent Getting Started](agents/GETTING_STARTED.md) - Comprehensive agent system guide
- [Architecture](agents/ARCHITECTURE.md) - Technical architecture and flow diagrams
- [Human Refinement Workflow](workflows/HUMAN_REFINEMENT.md) - Interactive refinement process
- [Evaluation Phase](workflows/EVALUATION_PHASE.md) - "Shark Tank" evaluation layer

### 🎤 Presenters & Stakeholders
- [Vision and Status](project/VISION_AND_STATUS.md) - Complete project vision, roadmap, and demo script
- [Architecture](agents/ARCHITECTURE.md) - Visual flow diagrams

### 📚 Historical Reference
- [Initial Specification](historical/INITIAL_SPEC.md) - Original 3-topic project spec

---

## Documentation Structure

### Setup Guides (`setup/`)
Essential guides for getting the system up and running.

- **[TERRAFORM_GUIDE.md](setup/TERRAFORM_GUIDE.md)** - Complete guide for deploying Confluent Cloud infrastructure
  - Prerequisites and Cloud API keys
  - Step-by-step deployment (~15-20 minutes)
  - Configuration options
  - Cost considerations (~$9-10/hour)
  - Troubleshooting

- **[ENVIRONMENT_CONFIG.md](setup/ENVIRONMENT_CONFIG.md)** - Environment configuration and credentials
  - Two-tier .env structure (root vs agents)
  - Cloud API Keys vs Cluster API Keys
  - Security best practices
  - Common authentication issues

### Agent Documentation (`agents/`)
Deep dive into the autonomous agent system.

- **[GETTING_STARTED.md](agents/GETTING_STARTED.md)** - Main agent system guide
  - Architecture overview
  - Quick start (dry-run vs full mode)
  - Individual agent usage
  - Directory structure
  - Troubleshooting

- **[ARCHITECTURE.md](agents/ARCHITECTURE.md)** - Technical architecture
  - Complete flow diagrams (Mermaid)
  - Layer-by-layer breakdown
  - Monitoring strategy
  - Feedback loops

### Workflow Guides (`workflows/`)
User interaction workflows and processes.

- **[HUMAN_REFINEMENT.md](workflows/HUMAN_REFINEMENT.md)** - Human-in-the-loop refinement
  - Complete flow from discovery to approval
  - Interactive workflow examples
  - Action demonstrations (approve, reject, edit, skip)
  - Key design principles

- **[EVALUATION_PHASE.md](workflows/EVALUATION_PHASE.md)** - Phase 3 "Shark Tank" evaluation
  - Iron triangle evaluation (scope/time/cost)
  - Agent personalities and outputs
  - Usage examples
  - Human approval interface

### Project Information (`project/`)
Vision, roadmap, and presentation materials.

- **[VISION_AND_STATUS.md](project/VISION_AND_STATUS.md)** - Complete project vision
  - End vision and demo journey
  - Phase-by-phase breakdown
  - Current status
  - 8-minute demo script
  - Key messages for different audiences
  - Q&A preparation

### Historical (`historical/`)
Archived documentation for reference.

- **[INITIAL_SPEC.md](historical/INITIAL_SPEC.md)** - Original project specification
  - Initial 3-topic plan (now expanded to 37)
  - Original vision and phases

---

## Common Tasks

### Setting Up for the First Time
1. Read [Vision and Status](project/VISION_AND_STATUS.md) to understand the project
2. Follow [Terraform Setup Guide](setup/TERRAFORM_GUIDE.md) to deploy infrastructure
3. Configure credentials with [Environment Configuration](setup/ENVIRONMENT_CONFIG.md)
4. Start agents with [Agent Getting Started](agents/GETTING_STARTED.md)

### Running the Agent Pipeline
1. Ensure infrastructure is deployed (Terraform)
2. Configure `agents/.env` with Kafka and Claude credentials
3. Run: `cd agents && ./venv/bin/python3 bootstrap.py`
4. Follow prompts in [Human Refinement Workflow](workflows/HUMAN_REFINEMENT.md)

### Understanding the Architecture
1. Start with [Architecture](agents/ARCHITECTURE.md) for visual flow diagrams
2. Read [Agent Getting Started](agents/GETTING_STARTED.md) for detailed explanations
3. Review [Evaluation Phase](workflows/EVALUATION_PHASE.md) for Phase 3 details

### Preparing a Demo
1. Review [Vision and Status](project/VISION_AND_STATUS.md) for demo script
2. Understand [Architecture](agents/ARCHITECTURE.md) for technical explanations
3. Practice [Human Refinement Workflow](workflows/HUMAN_REFINEMENT.md) interactions

### Troubleshooting
- **Terraform issues**: See [Terraform Setup Guide](setup/TERRAFORM_GUIDE.md) troubleshooting section
- **Authentication issues**: See [Environment Configuration](setup/ENVIRONMENT_CONFIG.md)
- **Agent issues**: See [Agent Getting Started](agents/GETTING_STARTED.md) troubleshooting section

---

## Cost Management

This system uses paid services. See these guides for cost management:
- [Terraform Setup Guide](setup/TERRAFORM_GUIDE.md) - Confluent Cloud costs (~$9-10/hour)
- [Agent Getting Started](agents/GETTING_STARTED.md) - Claude API costs

**Key Tip**: Use `terraform destroy` when not actively using the system to minimize costs.

---

## Contributing

Documentation improvements are welcome! When adding new documentation:
- Place it in the appropriate subdirectory (`setup/`, `agents/`, `workflows/`, `project/`)
- Update this README with a link and description
- Use clear, descriptive filenames in UPPER_SNAKE_CASE.md

---

## Questions?

- Check the troubleshooting sections in relevant guides
- Review [Vision and Status](project/VISION_AND_STATUS.md) for project context
- See [Initial Specification](historical/INITIAL_SPEC.md) for historical context
