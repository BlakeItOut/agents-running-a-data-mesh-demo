# Agentic Data Mesh Demo

**From Chaos to Clarity: Building a Data Mesh with an AI Agent Team**

A demonstration showcasing autonomous agents that transform raw, stream-based data into a product-oriented, discoverable data mesh.

## Overview

This project demonstrates how AI agents can automate the entire data product lifecycle—from design to operation—making the Data Mesh approach finally practical and scalable. A team of specialized agents work together to build production-ready data products in minutes instead of months.

### The Agent Team

- 🏗️ **The Architect**: Design and schema expert
- ⚙️ **The Engineer**: Infrastructure and bootstrapping specialist
- 💻 **The Coder**: Pair-programmer for business logic and testing
- 📚 **The Scribe**: Documentation and cataloging assistant
- 🔍 **The SRE**: Site Reliability Expert for observability

## Current Status

**Phase 1: Foundational Setup & Specification** ✅

- [x] Initial specification and architecture defined
- [x] Conference presentation infrastructure
- [ ] Agent implementation (planned)
- [ ] Terraform generation (planned)
- [ ] Live demo environment (planned)

## Data Environment

- **Platform**: Confluent Cloud
- **Sample Topics**: `users`, `orders`, `products`
- **Metadata Sources**: Schema Registry, usage metrics

## The Demo

The 45-minute presentation demonstrates each agent working through the complete data product lifecycle:

1. **Chapter 1 - The Blueprint**: The Architect designs the schema and data contract
2. **Chapter 2 - The Foundation**: The Engineer scaffolds infrastructure and opens a PR
3. **Chapter 3 - The Logic**: The Coder implements business logic and tests
4. **Chapter 4 - The Manual**: The Scribe documents and registers the data product
5. **Chapter 5 - The Watchtower**: The SRE creates observability infrastructure

Starting from a single prompt, the agents build a production-ready `user-authentication-events` data product with schema, Terraform configs, application code, tests, documentation, and monitoring—all reviewable via Pull Request.

## Key Principles

- **Specialization over Generalization**: A team of focused agents beats one generalist
- **Humans in the Loop**: Augmentation, not replacement—developers review and approve
- **Contribution First**: Agents generate PRs, not direct deployments
- **Built-in Governance**: Standards enforced by default, not bolted on afterward

## Contributing

This is a demonstration project. Feedback and suggestions welcome via issues.

## License

MIT
