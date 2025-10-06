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

## Presentation (Slides-as-Code)

This project uses a "slides-as-code" approach with Google Apps Script and clasp to programmatically generate the conference presentation.

### Building Slides Locally

```bash
# Install clasp globally
npm install -g @google/clasp

# Log in to Google
clasp login

# Create new Apps Script project (first time only)
cd slides-src
clasp create --title "Data Mesh Presentation Builder" --type standalone

# Push code to Apps Script
clasp push

# Build the presentation
clasp run buildPresentation
```

### Viewing Logs
```bash
clasp logs
```

### Automated Builds

GitHub Actions automatically builds the presentation on every push to `main`. The workflow:
1. Pushes Apps Script code to Google
2. Runs `buildPresentation` function
3. Generates new presentation in Google Drive

**Required Secrets** (for GitHub Actions):
- `CLASPRC_JSON`: Contents of `~/.clasprc.json` (clasp credentials)
- `CLASP_JSON`: Contents of `slides-src/.clasp.json` (Apps Script project ID)

### Presentation Structure

- **slides-src/Code.js**: Main entry point with helper functions
- **slides-src/config.js**: Theme configuration and constants
- **slides-src/content/**: Section-specific slide content
  - `intro.js`: Introduction slides
  - `problem.js`: Problem/chaos slides
  - `solution.js`: Solution/agent team slides
  - `demo.js`: Demo chapter slides
  - `conclusion.js`: Conclusion slides
- **docs/presentation-outline.md**: Full 45-minute presentation script with speaker notes

### Template

The presentation uses a colorful Google Slides template (ID: `10XqMMGWKuDichIWSMDeIw84KFgOSdZFS-5sv5avKYtk`) with:
- Yellow, coral, blue, and green color scheme
- Grid background texture
- macOS-style window frames
- Rounded callout shapes
