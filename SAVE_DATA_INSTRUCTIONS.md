# 💾 How to Save Your KPI Dashboard Data

## Quick Save (Easiest Method)

1. Open the dashboard: http://localhost:8000/kpi-dashboard.html
2. Click **"🔗 Connect to SharePoint"** (blue button)
3. Wait for **"✅ Connected"** status
4. Click **"💾 Save Data"** button
5. Done! ✅

## What Gets Saved:

### 📁 Location: `data secure/`

- **kpi-data.json** - Current data in JSON format
- **kpi-data.csv** - Current data in Excel format (ready to open!)
- **backups/** folder - Timestamped backups

### Example:
```
data secure/
├── kpi-data.json          ← Latest data
├── kpi-data.csv           ← Open in Excel!
└── backups/
    ├── kpi-data-20251108_151500.json
    ├── kpi-data-20251108_151500.csv
    ├── kpi-data-20251108_163000.json
    └── kpi-data-20251108_163000.csv
```

## Auto-Save Feature:

Your data is automatically saved:
- ✅ 2 seconds after editing any score
- ✅ When you click "Save Data"
- ✅ When you connect to SharePoint

## Check If Data is Saved:

```bash
# Check if files exist
ls -lh "data secure/"

# View the JSON file
cat "data secure/kpi-data.json"

# Open CSV in Excel
open "data secure/kpi-data.csv"
```

## Troubleshooting:

### ❌ "Backend not available"
**Solution:** Start the backend server:
```bash
cd /Users/galiaf/Library/CloudStorage/OneDrive-NVIDIACorporation/Cursor/KPI
python3 sharepoint_server.py
```

### ❌ No data appears after saving
**Solution:** 
1. Check browser console (F12) for errors
2. Make sure you entered data in the cells
3. Try clicking "Save Data" again

### ❌ Need to restore old data
**Solution:** 
1. Go to `data secure/backups/`
2. Find the backup you want (by timestamp)
3. Copy it to `data secure/kpi-data.json`
4. Reload the dashboard

## Manual Backup (Without Dashboard):

If you can't access the dashboard, you can manually export:

### Browser Console Method:
1. Open dashboard in browser
2. Press F12 (Developer Tools)
3. Go to Console tab
4. Type: `localStorage.getItem('kpiData')`
5. Copy the result and save it

---

Generated: 2025-11-08

