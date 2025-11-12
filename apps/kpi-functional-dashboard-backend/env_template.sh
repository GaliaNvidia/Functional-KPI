# Environment Variables for NAT blueprint
# Copy this file to env.sh file and source it in your terminal

echo "Setting environment variables for NAT React Agent Blueprint"

# NVIDIA API Configuration
export NATSP_REACT_NVIDIA_API_KEY=<nvidia_api_key>

# Datarobot API Configuration
export NATSP_REACT_DATAROBOT_API_KEY=<datarobot_api_key>

# ECI (Enterprise Content Intelligence) Configuration
# Required for the ECI search tool to function
export NATSP_REACT_ECI_CLIENT_ID=<eci_client_id>
export NATSP_REACT_ECI_CLIENT_SECRET=<eci_client_secret>

# PostgreSQL Database Configuration (Optional - for production deployments)
# Leave these unset if using local SQLite database
# Format: postgresql://username:password@host:port/database
export NATSP_REACT_POSTGRES_USER=<postgres_username>
export NATSP_REACT_POSTGRES_PASSWORD=<postgres_password>
export NATSP_REACT_POSTGRES_HOST=<postgres_host>      # e.g., wfo-astra-prd-rw.db.nvidia.com
export NATSP_REACT_POSTGRES_PORT=5432                     # Default PostgreSQL port
export NATSP_REACT_POSTGRES_DB=<postgres_database_name>   # e.g., astra_blueprints
export NATSP_REACT_POSTGRES_SCHEMA=<postgres_schema>      # e.g., northwind or public

# ============================================================================
# Milvus Vector Database Configuration (Optional - for production deployments)
# ============================================================================
# For local development, use ChromaDB (no configuration needed)
# For production, request IT-managed Milvus access using:
#   ~/milvus-cli show dev <your-cluster-name>
# You'll receive URI, username, and password

export NATSP_REACT_MILVUS_URI=<milvus_uri>                    # e.g., https://milvus-astra-users-dev.db.nvw.nvidia.com
export NATSP_REACT_MILVUS_USER=<milvus_user>                  # Use 'owner' or 'curator' for initial setup
export NATSP_REACT_MILVUS_PASSWORD=<milvus_password>          # Your Milvus password
export NATSP_REACT_MILVUS_COLLECTION=vanna_northwind_embeddings  # Milvus collection name for vector embeddings

# ============================================================================
# MCP Tool Configuration (Optional - for MaaS MCP servers like Jira, GitLab, etc.)
# These are used for OAuth2 authentication with MCP tools
# See: https://ipp-safety-tools.gitlab-master-pages.nvidia.com/giza-llm-tools/giza_ai/docs/tutorial/nat-quickstart

# NATSP_REACT_MCP_USER_ID: Used to cache authentication credentials (defaults to server URL if not set)
export NATSP_REACT_MCP_USER_ID=<your_nvidia_username>

# NATSP_REACT_MCP_ALLOW_DEFAULT_USER: Set to true for single-user mode (CLI), false for multi-user mode (server)
# Defaults to true if not provided
export NATSP_REACT_MCP_ALLOW_DEFAULT_USER=true

# NATSP_REACT_MCP_REDIRECT_URI: OAuth callback URL - must match where your NAT instance is accessible
# Defaults to http://localhost:8000/auth/redirect if not provided
# For remote servers, use: http://<your-server-ip>:8000/auth/redirect
export NATSP_REACT_MCP_REDIRECT_URI=http://localhost:8000/auth/redirect

# MaaS MCP Server URL (Required for MCP tool)
# Set this to the MaaS server you want to use
# Common options:
#   - Jira:       https://nvaihub.nvidia.com/maas/jira/mcp/
#   - GitLab:     https://nvaihub.nvidia.com/maas/gitlab/mcp/
#   - Confluence: https://nvaihub.nvidia.com/maas/confluence/mcp/
#   - Google Drive: https://nvaihub.nvidia.com/maas/gdrive/mcp/
#   - SharePoint: https://nvaihub.nvidia.com/maas/sharepoint/mcp/
#   - OneDrive:   https://nvaihub.nvidia.com/maas/onedrive/mcp/
export NATSP_REACT_MCP_SERVER_URL=<maas_server_url>


# Check if variables are set correctly
echo "Checking environment variables for NAT blueprint..."

if [ -z "$NATSP_REACT_NVIDIA_API_KEY" ]; then
  echo "NATSP_REACT_NVIDIA_API_KEY is NOT set!"
else
  echo "NATSP_REACT_NVIDIA_API_KEY is set."
fi

if [ -z "$NATSP_REACT_DATAROBOT_API_KEY" ]; then
  echo "NATSP_REACT_DATAROBOT_API_KEY is NOT set!"
else
  echo "NATSP_REACT_DATAROBOT_API_KEY is set."
fi

if [ -z "$NATSP_REACT_ECI_CLIENT_ID" ]; then
  echo "NATSP_REACT_ECI_CLIENT_ID is NOT set!"
else
  echo "NATSP_REACT_ECI_CLIENT_ID is set."
fi

if [ -z "$NATSP_REACT_ECI_CLIENT_SECRET" ]; then
  echo "NATSP_REACT_ECI_CLIENT_SECRET is NOT set!"
else
  echo "NATSP_REACT_ECI_CLIENT_SECRET is set."
fi

# PostgreSQL variables are optional
if [ ! -z "$NATSP_REACT_POSTGRES_USER" ]; then
  echo "PostgreSQL configuration detected:"
  echo "  - User: $NATSP_REACT_POSTGRES_USER"
  echo "  - Host: $NATSP_REACT_POSTGRES_HOST"
  echo "  - Database: $NATSP_REACT_POSTGRES_DB"
  echo "  - Schema: $NATSP_REACT_POSTGRES_SCHEMA"
else
  echo "PostgreSQL configuration NOT set (using local SQLite)"
fi

# Check for Milvus configuration (optional for production)
if [ ! -z "$NATSP_REACT_MILVUS_URI" ]; then
  echo "Milvus vector database configuration detected:"
  echo "  - URI: $NATSP_REACT_MILVUS_URI"
  echo "  - User: $NATSP_REACT_MILVUS_USER"
  echo "  - Collection: $NATSP_REACT_MILVUS_COLLECTION"
  echo "  - Password: [HIDDEN]"
  echo "  (Using IT-managed Milvus for production)"
else
  echo "Milvus configuration NOT set (using local ChromaDB)"
fi

# MCP variables are optional (except SERVER_URL which is required)
if [ ! -z "$NATSP_REACT_MCP_SERVER_URL" ]; then
  echo "MCP Tool configuration detected:"
  echo "  - Server URL: $NATSP_REACT_MCP_SERVER_URL"
  echo "  - User ID: $NATSP_REACT_MCP_USER_ID"
  echo "  - Redirect URI: $NATSP_REACT_MCP_REDIRECT_URI"
  echo "  - Allow default user: $NATSP_REACT_MCP_ALLOW_DEFAULT_USER"
else
  echo "MCP Tool configuration NOT set (NATSP_REACT_MCP_SERVER_URL required for MCP tool)"
fi