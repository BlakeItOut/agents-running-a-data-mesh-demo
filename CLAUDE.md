# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a demonstration project showcasing autonomous agents that transform raw, stream-based data into a product-oriented, discoverable data mesh. The project is in its **initial specification phase** (Phase 1).

### Core Concept

Agents autonomously:
1. Connect to Confluent Cloud topics (`users`, `orders`, `products`)
2. Analyze raw data streams using Schema Registry and usage metrics
3. Define and register data products based on bounded contexts
4. Generate Terraform configurations and data catalog entries

The demo illustrates how agents can convert siloed data streams into well-defined data products with proper ownership, schema, and access policies.

## Project Status

Currently in **Phase 1: Foundational Setup & Specification**
- Initial specification is defined in README.md
- Implementation of agents, Terraform generation, and demo presentation are planned for future phases

## Architecture Notes

### Data Environment
- **Platform**: Confluent Cloud
- **Initial Topics**: `users`, `orders`, `products` (Confluent sample data)
- **Metadata Sources**: Schema Registry, usage metrics

### Agentic Workflow
Agents will perform a three-stage autonomous workflow:
1. **Discovery & Ingestion**: Connect to Confluent topics and ingest streams
2. **Analysis & Enrichment**: Analyze structure, content, relationships using Schema Registry and usage metrics
3. **Data Product Definition**: Identify bounded contexts, generate Terraform configs and catalog entries

The key innovation is autonomous identification of data product boundaries from raw streams.

## Repository Structure

- `slides-src/` - Conference presentation infrastructure (see `slides-src/CLAUDE.md`)
- `docs/` - Documentation and presentation outline
- `.github/workflows/` - CI/CD automation
