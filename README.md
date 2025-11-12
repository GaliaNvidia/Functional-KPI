# Functional KPI Dashboard

A clean and visually appealing platform for tracking KPI scores across quarters with automatic color coding.

| latest version | type | description |
| --- | --- | --- |
| [![kpi-functional-dashboard-backend](https://gitlab-master.nvidia.com/ape-repo/astra-projects/kpi-dash/-/jobs/artifacts/main/raw/public/badges/app-kpi-functional-dashboard-backend.svg?job=multi_release:finalize)](https://gitlab-master.nvidia.com/ape-repo/astra-projects/kpi-dash/-/jobs/artifacts/main/raw/public/badges/app-kpi-functional-dashboard-backend.svg?job=multi_release:finalize) | [![PyPI](https://img-shield-cloudsre.gcp-int.nvidia.com/badge/PyPI-3775A9?logo=pypi&logoColor=fff)](#) | NAT React Agent Blueprint for Astra |

🛑 This table is automatically generated. Please do not modify it!!!

## Features

✨ **Easy Data Entry**: Click any cell to edit scores
🎨 **Automatic Color Coding**: Scores are color-coded based on Min/Target/Stretch thresholds
- 🔴 Red: Below minimum threshold
- 🟡 Yellow: Between minimum and target
- 🟢 Green: At or above target (stretch goal)

💾 **Persistent Storage**: All scores are automatically saved in your browser
📊 **Last 4 Quarters**: Always displays the most recent four quarters
📋 **Copy to Clipboard**: Easy one-click copy for pasting into presentations
📈 **Export to CSV**: Download your data for further analysis
🗑️ **Clear Data**: Reset all data when needed

## How to Use

### Getting Started
1. Open `index.html` in your web browser
2. The dashboard will load with sample data

### Adding Scores
1. Click on any cell in the quarter columns
2. Type the score value
3. Press Enter or click outside to save
4. The cell will automatically color-code based on thresholds

### Adding a New Quarter
1. Click the "➕ Add Quarter" button
2. Enter the quarter name (e.g., Q4FY26)
3. Click "Add Quarter"
4. The table will automatically show the last 4 quarters

### Copying to Presentations
1. Click "📋 Copy to Clipboard"
2. Open your presentation software (PowerPoint, Google Slides, etc.)
3. Press Ctrl+V (or Cmd+V on Mac) to paste

### Exporting Data
1. Click "📊 Export to CSV"
2. The file will download automatically
3. Open in Excel, Google Sheets, or any spreadsheet software

## Color Coding Rules

The system uses the thresholds defined for each metric:

**For Percentage Metrics** (e.g., On Time Delivery):
- Score < Min (98%): 🔴 Red
- Score >= Min but < Target (100%): 🟡 Yellow  
- Score >= Target: 🟢 Green

**For Rating Metrics** (1-5 scale):
- Score < Min (4): 🔴 Red
- Score >= Min but < Target (5): 🟡 Yellow
- Score >= Target: 🟢 Green

## Technical Details

- **Frontend**: React 18
- **Storage**: Browser localStorage
- **No Backend Required**: All data is stored locally
- **Responsive Design**: Works on desktop and tablet devices

## Data Persistence

All data is automatically saved to your browser's localStorage. This means:
- ✅ Data persists between sessions
- ✅ No internet connection required
- ⚠️ Data is specific to the browser you're using
- ⚠️ Clearing browser data will clear your KPI data

## Customization

The metrics are pre-configured based on your requirements. To modify metrics, edit the `DEFAULT_METRICS` array in `app.js`.

## Browser Compatibility

Works in all modern browsers:
- Chrome/Edge (recommended)
- Firefox
- Safari

---

## 📁 Repository Structure

**`apps/`** - Source code for containerized applications. Each subdirectory represents a separate microservice with its own Dockerfile and dependencies.

## 🚀 CI/CD Pipeline

The GitLab CI pipeline will automatically:
- Build Docker images for each application in the `apps/` directory
- Tag images with version numbers
- Push images to JFrog Artifactory (`artifactory.nvidia.com/continum`)
- Generate release badges and version tracking

### Image Naming Convention

Images will be published to JFrog with the following naming pattern:
- `artifactory.nvidia.com/continum/kpi-functional-dashboard:{version}`

Where `{version}` follows semantic versioning (e.g., 1.0.0, 1.0.1, etc.)

## 🔧 Configuration

- **Dockerfile**: Each app directory contains a Dockerfile that you can customize for your application's specific needs
- **requirements.txt / package.json**: Update dependencies as needed for your technology stack
- **version.py**: Version numbers are automatically managed by the CI/CD pipeline
- **.gitlab-ci.yml**: CI/CD configuration is managed at the repository level

## 📊 Monitoring & Access

### Accessing Built Images
Once built, your Docker images will be available at:
```
artifactory.nvidia.com/it-continum/kpi-functional-dashboard:{specific-version}
```

## Maintainers
Galia Plotinsky - galiaf@nvidia.com

---

**Note**: The main KPI Dashboard is a client-side application with no server backend. All data is stored locally in your browser.
