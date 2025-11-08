📁 KPI DASHBOARD - DATA SECURE FOLDER
=====================================

This folder contains automatic backups of your KPI Dashboard data.

📄 FILES:
---------
• kpi-data.json      - Latest/current KPI data (JSON format)
• kpi-data.csv       - Latest/current KPI data (Excel-compatible CSV)
• backups/           - Timestamped backup files (JSON + CSV)

💾 HOW IT WORKS:
----------------
Every time you save data in the KPI Dashboard:
1. Data is saved to "kpi-data.json" (JSON format)
2. Data is saved to "kpi-data.csv" (Excel-compatible format)
3. Timestamped backups are created in "backups" folder (both formats)
4. Data is also sent to SharePoint (when configured)

🔄 AUTO-SAVE:
-------------
The dashboard automatically saves your changes:
• 2 seconds after you edit any score
• When you click "Save Data" button
• When you connect to SharePoint

📦 BACKUPS:
-----------
Backup files are timestamped:
• JSON: kpi-data-YYYYMMDD_HHMMSS.json
• CSV:  kpi-data-YYYYMMDD_HHMMSS.csv

Example: kpi-data-20251108_145800.json

You can restore from any backup by:
1. Copying a backup file
2. Renaming it to "kpi-data.json" (or .csv)
3. Reloading the dashboard

📊 EXCEL FORMAT:
----------------
The CSV file can be opened directly in:
• Microsoft Excel
• Google Sheets
• Apple Numbers
• Any spreadsheet application

The structure matches the dashboard:
Category | Metric | CM | Product Line | Min | Target | Stretch | Q1'25 | Q2'25 | ...

🔒 SECURITY:
------------
• This folder is in your OneDrive (synced automatically)
• All backups are kept for your records
• No data is lost even if SharePoint is unavailable

✅ LOCATION:
------------
/Users/galiaf/Library/CloudStorage/OneDrive-NVIDIACorporation/Cursor/KPI/data secure/

Generated: 2025-11-08
KPI Dashboard Backend v1.0

