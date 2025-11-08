# SharePoint MCP Integration - Setup Guide

## ✅ What's Implemented

Your KPI Dashboard now has **SharePoint auto-save** using SharePoint MCP! Here's what it does:

- 🔄 **Auto-saves** data to SharePoint 2 seconds after any change
- 📥 **Auto-loads** data from SharePoint when you open the dashboard
- 👥 **Team collaboration** - everyone with access sees the same data
- 💾 **Dual storage** - Local backup + SharePoint cloud storage
- 📊 **CSV format** - Data saved as `KPI_Dashboard_Data.csv`
- 🔐 **No configuration needed** - Uses your NVIDIA SSO automatically

## 🚀 Quick Start (3 minutes)

### Option 1: Automated Start (Easiest)

Run the startup script that starts both servers:

```bash
./start-sharepoint.sh
```

Then open in your browser:
```
http://localhost:8000/kpi-dashboard.html
```

### Option 2: Manual Start

**Terminal 1 - Start SharePoint Backend:**
```bash
node sharepoint-server.js
```

**Terminal 2 - Start Dashboard Server:**
```bash
python3 -m http.server 8000
```

**Browser:**
```
http://localhost:8000/kpi-dashboard.html
```

---

## 📖 How It Works

### Architecture

```
┌─────────────┐         ┌──────────────┐         ┌──────────────┐
│   Browser   │ ◄─────► │   Backend    │ ◄─────► │  SharePoint  │
│  Dashboard  │  HTTP   │   Server     │   MCP   │   (NVIDIA)   │
└─────────────┘         └──────────────┘         └──────────────┘
                         (Port 3000)
```

1. **Dashboard** (frontend) runs in your browser
2. **Backend server** (Node.js) provides API endpoints
3. **SharePoint MCP** handles authentication and file operations
4. **Your NVIDIA credentials** are used automatically (SSO)

### Auto-Save Behavior

- Data saves **locally** immediately when you edit
- Data saves to **SharePoint** 2 seconds after your last change
- This prevents excessive API calls while you're typing
- Status shows in the toast notification

### File Location

Your data is saved to:
```
https://nvidia.sharepoint.com/sites/QBRmanagement/Shared Documents/KPI_Dashboard_Data.csv
```

### Team Collaboration

- Everyone who connects sees the **same data**
- Last save wins (similar to Google Docs)
- Data syncs when you:
  - Open the dashboard
  - Click "Save Data"
  - Edit any score (auto-saves after 2 seconds)

### Connection Status

Look for the status indicator next to the "Connect to SharePoint" button:

- **✅ Connected** - SharePoint sync is active
- **⚠️ Backend not available** - Server not running, using local storage
- **❌ Not connected** - Connection failed, using local storage

---

## 🔧 Backend API Endpoints

The Node.js server provides these endpoints:

- `GET  /api/sharepoint/health` - Health check
- `POST /api/sharepoint/save` - Save data to SharePoint
- `POST /api/sharepoint/load` - Load data from SharePoint

---

## 🎯 Usage

### First Time Setup

1. Start the servers (using `./start-sharepoint.sh` or manually)
2. Open dashboard in browser
3. Dashboard automatically checks if backend is available
4. If available, click "🔗 Connect to SharePoint"
5. Data auto-loads from SharePoint (if file exists)

### Daily Use

1. Start servers
2. Open dashboard
3. Edit data as normal
4. Data auto-saves to SharePoint
5. Team members see your updates

### Offline Mode

- If backend isn't running, dashboard works normally with localStorage
- Start backend later to sync
- No data is lost

---

## 🔧 Troubleshooting

### "Backend not available" message

**Cause**: SharePoint server not running

**Fix**: 
```bash
node sharepoint-server.js
```
Or use `./start-sharepoint.sh`

### Data not syncing between users

**Cause**: Each user needs their own running servers

**Fix**: Each team member should run the servers locally. In production, deploy to a shared server.

### Port already in use

**Backend (3000):**
```bash
# Find what's using port 3000
lsof -i :3000
# Kill it or change port in sharepoint-server.js
```

**Frontend (8000):**
```bash
# Use a different port
python3 -m http.server 8001
# Then open http://localhost:8001/kpi-dashboard.html
```

---

## 🚀 Production Deployment

For team-wide use, deploy the backend server to a shared location:

### Option 1: Deploy to Azure/AWS/GCP

1. Deploy `sharepoint-server.js` to a cloud VM
2. Update `kpi-dashboard.html` API endpoints to point to your server
3. Set up HTTPS with SSL certificate
4. Configure firewall rules

### Option 2: NVIDIA Internal Server

1. Deploy to an NVIDIA internal server
2. Ensure server has Node.js installed
3. Run as a service (using systemd or similar)
4. Update dashboard URL in `kpi-dashboard.html`

### Example Production Config

In `kpi-dashboard.html`, change:
```javascript
const response = await fetch('/api/sharepoint/health', { method: 'GET' });
```

To:
```javascript
const response = await fetch('https://your-server.nvidia.com/api/sharepoint/health', { method: 'GET' });
```

---

## 📝 Configuration

### Change SharePoint Site

Edit `sharepoint-server.js`:
```javascript
const SHAREPOINT_SITE_URL = 'https://nvidia.sharepoint.com/sites/YOUR_SITE/';
```

Edit `kpi-dashboard.html`:
```javascript
const SHAREPOINT_CONFIG = {
    siteUrl: 'https://nvidia.sharepoint.com/sites/YOUR_SITE/',
    fileName: 'KPI_Dashboard_Data.csv',
    fileUrl: 'https://nvidia.sharepoint.com/sites/YOUR_SITE/Shared%20Documents/KPI_Dashboard_Data.csv',
    autoSaveDelay: 2000
};
```

### Change Auto-Save Delay

Edit `kpi-dashboard.html`:
```javascript
autoSaveDelay: 5000 // 5 seconds instead of 2
```

---

## 🔐 Security

- **Authentication**: Uses your NVIDIA SSO credentials automatically
- **Authorization**: Respects SharePoint permissions
- **Data**: Stored in NVIDIA SharePoint (secure)
- **Transport**: Uses HTTPS for production deployments

---

## 📚 Files Created

- `sharepoint-server.js` - Backend server
- `start-sharepoint.sh` - Startup script
- `SHAREPOINT_SETUP.md` - This guide

---

## 🆘 Need Help?

### Check Server Status

```bash
# Is backend running?
curl http://localhost:3000/api/sharepoint/health

# Expected response:
# {"status":"healthy","message":"SharePoint MCP backend is running","timestamp":"..."}
```

### View Server Logs

The Node.js server outputs logs to console:
- 📊 Health checks
- 💾 Save operations
- 📥 Load operations
- ❌ Errors

### Common Issues

**Q: Can multiple users edit simultaneously?**
A: Yes, but last save wins. For real-time collaboration, consider adding conflict resolution.

**Q: What if SharePoint is down?**
A: Dashboard continues working with local storage. Data syncs when SharePoint is back.

**Q: How much data can be saved?**
A: SharePoint file size limits apply (typically 250MB+), which is more than enough for this dashboard.

---

**Created**: November 8, 2025  
**Updated**: November 8, 2025  
**Version**: 2.0 (SharePoint MCP)
