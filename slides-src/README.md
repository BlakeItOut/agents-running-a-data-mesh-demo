# Slides-as-Code: Google Apps Script Setup

This directory contains Google Apps Script code that programmatically generates the presentation for the Data Mesh Agent demo.

## Structure

```
slides-src/
├── Code.js              # Main entry point with helper functions
├── config.js            # Theme configuration and constants
├── appsscript.json      # Apps Script manifest
└── content/
    ├── intro.js         # Introduction slides
    ├── problem.js       # Problem/chaos slides
    ├── solution.js      # Solution/agent team slides
    ├── demo.js          # Demo chapter slides
    └── conclusion.js    # Conclusion slides
```

## Setup Instructions

### 1. Enable Apps Script API

1. Go to https://script.google.com/home/usersettings
2. Turn on "Google Apps Script API"

### 2. Install clasp

```bash
npm install -g @google/clasp
```

### 3. Log in to clasp

```bash
clasp login
```

This will open a browser window for authentication.

### 4. Create a new Apps Script project

```bash
cd slides-src
clasp create --title "Data Mesh Presentation Builder" --type standalone
```

This will create a `.clasp.json` file with your script ID.

### 5. Push the code to Apps Script

```bash
clasp push
```

### 6. Run the presentation builder

```bash
clasp run buildPresentation
```

Or run it from the Apps Script web editor:
1. Go to https://script.google.com
2. Open your project
3. Select `buildPresentation` from the function dropdown
4. Click Run

## GitHub Actions Setup

To automate slide generation on every push:

### 1. Get your clasp credentials

After running `clasp login`, find the `.clasprc.json` file:
- **Windows**: `C:\Users\YourUser\.clasprc.json`
- **Mac/Linux**: `~/.clasprc.json`

### 2. Create GitHub Secrets

In your GitHub repository:
1. Go to **Settings → Secrets and variables → Actions**
2. Create two secrets:
   - `CLASPRC_JSON`: Paste the entire contents of `.clasprc.json`
   - `CLASP_JSON`: Paste the contents of `.clasp.json` from the `slides-src` directory

### 3. Push to main

The workflow in `.github/workflows/build-slides.yml` will automatically:
- Push your Apps Script code
- Run the `buildPresentation` function
- Generate a new presentation in your Google Drive

## Local Development

### Run the function locally
```bash
cd slides-src
clasp run buildPresentation
```

### Watch for changes and auto-push
```bash
cd slides-src
clasp push --watch
```

### View logs
```bash
clasp logs
```

## Modifying the Presentation

1. Edit content in the `content/` directory (intro.js, problem.js, etc.)
2. Modify theme/colors in `config.js`
3. Add new helper functions in `Code.js`
4. Push changes with `clasp push`
5. Run `buildPresentation` to generate a new deck

## Template Theme

The presentation uses the template from:
https://docs.google.com/presentation/d/10XqMMGWKuDichIWSMDeIw84KFgOSdZFS-5sv5avKYtk/edit

To use a different template, update `THEME_PRESENTATION_ID` in `config.js`.
