# Slides Source - CLAUDE.md

This directory contains Google Apps Script code for programmatically generating the conference presentation.

## Overview

The presentation is built using a "slides-as-code" approach with Google Apps Script and clasp. This ensures slides stay in sync with project documentation as they evolve.

## Local Development

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
# Note: Run from Apps Script web editor at script.google.com
# Select buildPresentation function and click Run
```

### Viewing Logs
```bash
clasp logs
```

## Automated Builds

GitHub Actions automatically builds the presentation on every push to `main` via a webhook endpoint.

### How it works:
1. GitHub Actions pushes code to Apps Script with `clasp push`
2. GitHub Actions POSTs to the deployed web app endpoint
3. Web app validates secret token and triggers `buildPresentation()`
4. New presentation is generated in Google Drive

### Setup Requirements:

**Apps Script Deployment**:
1. Deploy the script as a Web App (Deploy → New deployment → Web app)
2. Set "Execute as: Me" and "Who has access: Anyone"
3. Add `WEBHOOK_SECRET` to Script Properties with a random token

**GitHub Secrets**:
- `CLASPRC_JSON`: Contents of `~/.clasprc.json` (clasp credentials)
- `CLASP_JSON`: Contents of `slides-src/.clasp.json` (Apps Script project ID)
- `SLIDES_WEBHOOK_URL`: The deployed web app URL
- `SLIDES_WEBHOOK_SECRET`: Same value as the Script Property

## Code Structure

- **Code.js**: Main entry point with helper functions for creating slides
- **config.js**: Theme configuration, colors, and presentation metadata
- **appsscript.json**: Apps Script manifest with Slides API enabled
- **content/**: Section-specific slide content
  - `intro.js`: Introduction slides (~10 min)
  - `problem.js`: Problem/chaos slides (~10 min)
  - `solution.js`: Solution/agent team slides (~5 min)
  - `demo.js`: Demo chapter slides (~25 min)
  - `conclusion.js`: Conclusion slides (~5 min)

## Presentation Template

Uses Google Slides template ID: `10XqMMGWKuDichIWSMDeIw84KFgOSdZFS-5sv5avKYtk`

**Theme**:
- Yellow, coral, blue, and green color scheme
- Grid background texture
- macOS-style window frames
- Rounded callout shapes

## Modifying Content

1. Edit content in `content/*.js` files
2. Update theme/colors in `config.js`
3. Add new helper functions in `Code.js`
4. Run `clasp push` to sync changes
5. Execute `buildPresentation` to regenerate slides

The full 45-minute presentation script with speaker notes is in `../docs/presentation-outline.md`.
