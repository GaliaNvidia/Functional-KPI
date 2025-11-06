# Functional KPI Dashboard

A clean and visually appealing platform for tracking KPI scores across quarters with automatic color coding.

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

**Note**: This is a client-side application with no server backend. All data is stored locally in your browser.
