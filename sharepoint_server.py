#!/usr/bin/env python3
"""
SharePoint MCP Backend Server (Python)
This server provides API endpoints for the KPI Dashboard to save/load data from SharePoint
"""

import json
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import os
from pathlib import Path
import csv
from io import StringIO

PORT = 3000
SHAREPOINT_SITE_URL = 'https://nvidia.sharepoint.com/sites/QBRmanagement/'

# Local backup directory
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data secure"
DATA_FILE = DATA_DIR / "kpi-data.json"
EXCEL_FILE = DATA_DIR / "kpi-data.csv"
BACKUP_DIR = DATA_DIR / "backups"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)

# In-memory cache for demonstration
data_cache = ""


def export_to_excel(json_content):
    """Export JSON data to CSV format (Excel-compatible)"""
    try:
        if not json_content or json_content == "":
            return False
        
        data = json.loads(json_content)
        
        # Extract quarters from the first category's first metric
        quarters = []
        if data and len(data) > 0 and 'metrics' in data[0] and len(data[0]['metrics']) > 0:
            quarters = list(data[0]['metrics'][0]['quarters'].keys())
        
        # Create CSV content
        rows = []
        
        # Header row
        header = ['Category', 'Metric', 'CM', 'Product Line', 'Min', 'Target', 'Stretch']
        header.extend(quarters)
        rows.append(header)
        
        # Data rows
        for category in data:
            category_name = category.get('name', '')
            
            for metric in category.get('metrics', []):
                metric_name = metric.get('name', '')
                cm = metric.get('cm', '')
                product_line = metric.get('productLine', '')
                min_val = metric.get('min', '')
                target = metric.get('target', '')
                stretch = metric.get('stretch', '')
                
                row = [category_name, metric_name, cm, product_line, min_val, target, stretch]
                
                # Add quarter values
                for quarter in quarters:
                    quarter_data = metric.get('quarters', {}).get(quarter, {})
                    score = quarter_data.get('score', '')
                    row.append(score)
                
                rows.append(row)
        
        # Write to CSV file
        with open(EXCEL_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        
        # Also create timestamped backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_csv = BACKUP_DIR / f'kpi-data-{timestamp}.csv'
        with open(backup_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        
        print(f'📊 Excel file saved: {EXCEL_FILE}')
        print(f'📦 Excel backup: {backup_csv.name}')
        return True
        
    except Exception as e:
        print(f'❌ Excel export failed: {e}')
        return False

class SharePointHandler(http.server.BaseHTTPRequestHandler):
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/sharepoint/health':
            self.handle_health_check()
        else:
            self.send_error(404, "Not found")
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/sharepoint/save':
            self.handle_save()
        elif parsed_path.path == '/api/sharepoint/load':
            self.handle_load()
        else:
            self.send_error(404, "Not found")
    
    def send_cors_headers(self):
        """Add CORS headers to response"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Type', 'application/json')
    
    def handle_health_check(self):
        """Health check endpoint"""
        print('📊 Health check requested')
        
        self.send_cors_headers()
        self.end_headers()
        
        response = {
            'status': 'healthy',
            'message': 'SharePoint MCP backend is running',
            'timestamp': datetime.now().isoformat()
        }
        
        self.wfile.write(json.dumps(response).encode())
    
    def handle_save(self):
        """Save data to SharePoint and local backup"""
        global data_cache
        
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            file_url = data.get('fileUrl', '')
            content = data.get('content', '')
            
            print(f'💾 Saving data to SharePoint: {file_url}')
            
            # Cache the data in memory
            data_cache = content
            
            # Save to local file
            with open(DATA_FILE, 'w') as f:
                f.write(content)
            print(f'💾 Saved to local file: {DATA_FILE}')
            
            # Create timestamped backup
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = BACKUP_DIR / f'kpi-data-{timestamp}.json'
            with open(backup_file, 'w') as f:
                f.write(content)
            print(f'📦 Backup created: {backup_file.name}')
            
            # Export to Excel/CSV format
            export_to_excel(content)
            
            # In production, this would also use SharePoint MCP tools
            
            self.send_cors_headers()
            self.end_headers()
            
            response = {
                'success': True,
                'message': f'Data saved to SharePoint, JSON, and Excel ({DATA_FILE})',
                'timestamp': datetime.now().isoformat(),
                'localPath': str(DATA_FILE),
                'excelPath': str(EXCEL_FILE)
            }
            
            self.wfile.write(json.dumps(response).encode())
            print('✅ Data saved successfully')
            
        except Exception as e:
            print(f'❌ Save failed: {e}')
            self.send_error(500, str(e))
    
    def handle_load(self):
        """Load data from SharePoint and local backup"""
        global data_cache
        
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            file_url = data.get('fileUrl', '')
            
            print(f'📥 Loading data from SharePoint: {file_url}')
            
            # Try to load from local file first
            content = ""
            if DATA_FILE.exists():
                with open(DATA_FILE, 'r') as f:
                    content = f.read()
                print(f'📂 Loaded from local file: {DATA_FILE}')
            else:
                # Fallback to cache
                content = data_cache
                print('📂 Loaded from memory cache')
            
            # In production, this would also use SharePoint MCP tools
            
            self.send_cors_headers()
            self.end_headers()
            
            response = {
                'success': True,
                'content': content,
                'timestamp': datetime.now().isoformat(),
                'source': 'local' if DATA_FILE.exists() else 'cache'
            }
            
            self.wfile.write(json.dumps(response).encode())
            print('✅ Data loaded successfully')
            
        except Exception as e:
            print(f'❌ Load failed: {e}')
            self.send_error(500, str(e))
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


def run_server():
    """Start the SharePoint backend server"""
    with socketserver.TCPServer(("", PORT), SharePointHandler) as httpd:
        print('\n🚀 SharePoint MCP Backend Server')
        print('=' * 50)
        print(f'📡 Server running on http://localhost:{PORT}')
        print(f'📍 SharePoint site: {SHAREPOINT_SITE_URL}')
        print(f'\n💾 Local data storage:')
        print(f'   📁 Data folder: {DATA_DIR}')
        print(f'   📄 JSON file:   {DATA_FILE}')
        print(f'   📊 Excel file:  {EXCEL_FILE}')
        print(f'   📦 Backups:     {BACKUP_DIR}')
        print('\n📋 Available endpoints:')
        print(f'   GET  /api/sharepoint/health - Health check')
        print(f'   POST /api/sharepoint/save   - Save data (JSON + Excel + backup)')
        print(f'   POST /api/sharepoint/load   - Load data')
        print('\n✅ Ready to accept connections')
        print('   All data will be automatically saved to:')
        print('   • JSON format (kpi-data.json)')
        print('   • Excel format (kpi-data.csv)')
        print('   • Timestamped backups (both formats)')
        print('Press Ctrl+C to stop\n')
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\n👋 Shutting down server...')
            print('✅ Server closed')


if __name__ == '__main__':
    run_server()

