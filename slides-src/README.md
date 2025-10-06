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

### 6. Deploy as Web App (for GitHub Actions automation)

1. Go to https://script.google.com and open your project
2. Click **Deploy** → **New deployment**
3. Select type: **Web app**
4. Configure:
   - Execute as: **Me**
   - Who has access: **Anyone**
5. Click **Deploy**
6. Copy the **Web app URL**
7. In the Apps Script editor: **File** → **Project properties** → **Script properties**
8. Add property: `WEBHOOK_SECRET` with a random token value (generate with `openssl rand -hex 32`)

### 7. Run the presentation builder

From the Apps Script web editor:
1. Go to https://script.google.com
2. Open your project
3. Select `buildPresentation` from the function dropdown
4. Click Run

## GitHub Actions Setup

To automate slide generation on every push to `main`:

### 1. Set up the Web App (see step 6 above)

Make sure you've deployed the Apps Script as a web app and configured the `WEBHOOK_SECRET` in Script Properties.

### 2. Get your clasp credentials

After running `clasp login`, find the `.clasprc.json` file:
- **Windows**: `C:\Users\YourUser\.clasprc.json`
- **Mac/Linux**: `~/.clasprc.json`

### 3. Create GitHub Secrets

In your GitHub repository:
1. Go to **Settings → Secrets and variables → Actions**
2. Create these secrets:
   - `CLASPRC_JSON`: Paste the entire contents of `.clasprc.json`
   - `CLASP_JSON`: Paste the contents of `slides-src/.clasp.json`
   - `SLIDES_WEBHOOK_URL`: The web app URL from deployment (step 6.6)
   - `SLIDES_WEBHOOK_SECRET`: The same secret token from Script Properties (step 6.8)

### 4. Push to main

The workflow in `.github/workflows/build-slides.yml` will automatically:
1. Push your Apps Script code to Google
2. Call the web app endpoint to trigger `buildPresentation`
3. Generate a new presentation in your Google Drive

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
