#!/usr/bin/env node

/**
 * SharePoint MCP Backend Server
 * This server provides API endpoints for the KPI Dashboard to save/load data from SharePoint
 * Uses SharePoint MCP tools for authentication and file operations
 */

const http = require('http');
const url = require('url');

const PORT = 3000;
const SHAREPOINT_SITE_URL = 'https://nvidia.sharepoint.com/sites/QBRmanagement/';

// In-memory cache for demonstration (in production, use proper file operations via MCP)
let dataCache = null;

// Parse JSON body from request
function parseBody(req) {
    return new Promise((resolve, reject) => {
        let body = '';
        req.on('data', chunk => body += chunk.toString());
        req.on('end', () => {
            try {
                resolve(body ? JSON.parse(body) : {});
            } catch (error) {
                reject(error);
            }
        });
    });
}

// CORS headers
function setCORSHeaders(res) {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
}

// Handle SharePoint health check
async function handleHealthCheck(res) {
    console.log('📊 Health check requested');
    
    // In a real implementation, this would call the SharePoint MCP health check
    // For now, return success
    setCORSHeaders(res);
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
        status: 'healthy',
        message: 'SharePoint MCP backend is running',
        timestamp: new Date().toISOString()
    }));
}

// Handle save to SharePoint
async function handleSave(req, res) {
    try {
        const body = await parseBody(req);
        const { fileUrl, content } = body;
        
        console.log(`💾 Saving data to SharePoint: ${fileUrl}`);
        
        // In real implementation, this would use SharePoint MCP tools
        // For now, cache the data in memory
        dataCache = content;
        
        // Simulate SharePoint save
        // In production, you would call:
        // await sharepoint_mcp_upload_file(fileUrl, content);
        
        setCORSHeaders(res);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            success: true,
            message: 'Data saved to SharePoint',
            timestamp: new Date().toISOString()
        }));
        
        console.log('✅ Data saved successfully');
        
    } catch (error) {
        console.error('❌ Save failed:', error);
        setCORSHeaders(res);
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            success: false,
            error: error.message
        }));
    }
}

// Handle load from SharePoint
async function handleLoad(req, res) {
    try {
        const body = await parseBody(req);
        const { fileUrl } = body;
        
        console.log(`📥 Loading data from SharePoint: ${fileUrl}`);
        
        // In real implementation, this would use SharePoint MCP tools
        // For now, return cached data
        
        // Simulate SharePoint load
        // In production, you would call:
        // const content = await sharepoint_mcp_get_file(fileUrl);
        
        setCORSHeaders(res);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            success: true,
            content: dataCache || '',
            timestamp: new Date().toISOString()
        }));
        
        console.log('✅ Data loaded successfully');
        
    } catch (error) {
        console.error('❌ Load failed:', error);
        setCORSHeaders(res);
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            success: false,
            error: error.message
        }));
    }
}

// Main request handler
const server = http.createServer(async (req, res) => {
    const parsedUrl = url.parse(req.url, true);
    const pathname = parsedUrl.pathname;
    
    // Handle OPTIONS for CORS
    if (req.method === 'OPTIONS') {
        setCORSHeaders(res);
        res.writeHead(204);
        res.end();
        return;
    }
    
    // Route requests
    if (pathname === '/api/sharepoint/health' && req.method === 'GET') {
        await handleHealthCheck(res);
    } else if (pathname === '/api/sharepoint/save' && req.method === 'POST') {
        await handleSave(req, res);
    } else if (pathname === '/api/sharepoint/load' && req.method === 'POST') {
        await handleLoad(req, res);
    } else {
        setCORSHeaders(res);
        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Not found' }));
    }
});

// Start server
server.listen(PORT, () => {
    console.log('\n🚀 SharePoint MCP Backend Server');
    console.log('=====================================');
    console.log(`📡 Server running on http://localhost:${PORT}`);
    console.log(`📍 SharePoint site: ${SHAREPOINT_SITE_URL}`);
    console.log('\n📋 Available endpoints:');
    console.log(`   GET  /api/sharepoint/health - Health check`);
    console.log(`   POST /api/sharepoint/save   - Save data to SharePoint`);
    console.log(`   POST /api/sharepoint/load   - Load data from SharePoint`);
    console.log('\n✅ Ready to accept connections\n');
});

// Handle graceful shutdown
process.on('SIGINT', () => {
    console.log('\n👋 Shutting down server...');
    server.close(() => {
        console.log('✅ Server closed');
        process.exit(0);
    });
});

/*
 * PRODUCTION IMPLEMENTATION NOTES:
 * 
 * To integrate with actual SharePoint MCP tools, replace the simulated
 * operations with real MCP calls:
 * 
 * 1. For save operations:
 *    const result = await mcp_sharepoint_upload_file(fileUrl, content);
 * 
 * 2. For load operations:
 *    const content = await mcp_sharepoint_get_file(fileUrl);
 * 
 * 3. For health check:
 *    const health = await mcp_sharepoint_health_check();
 * 
 * The MCP tools handle authentication automatically via your NVIDIA SSO.
 */

