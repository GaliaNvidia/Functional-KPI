#!/bin/bash
# Script to push environment variables to NVIDIA Vault
# Usage: ./push_to_vault.sh [app-name]
# Example: ./push_to_vault.sh my-custom-app
# Default: nat-react-agent-blueprint

set -e

# Get app name from argument or use default
APP_NAME="${1:-nat-react-agent-blueprint}"

echo "============================================================================"
echo "PUSHING CREDENTIALS TO NVIDIA VAULT"
echo "============================================================================"
echo ""
echo "App Name: $APP_NAME"
echo "Target Path: KVv2/it-continuum/prd/$APP_NAME"
echo ""

# Source the environment variables
if [ -f "env.sh" ]; then
    source env.sh
    echo "✅ Loaded environment variables from env.sh"
else
    echo "❌ Error: env.sh not found!"
    exit 1
fi

# Check if vault CLI is installed
if ! command -v vault &> /dev/null; then
    echo ""
    echo "❌ Vault CLI not found. Please install it first:"
    echo ""
    echo "curl https://urm.nvidia.com/artifactory/sw-kaizen-data-generic/com/nvidia/vault/vault-agent/2.4.4/nvault_agent_v2.4.4_darwin_universal.zip -o vault.zip"
    echo "unzip vault.zip && sudo mv vault /usr/local/bin/ && chmod 755 /usr/local/bin/vault"
    echo ""
    exit 1
fi

echo "✅ Vault CLI found"
echo ""

export VAULT_ADDR=https://prod.internal.vault.nvidia.com
export VAULT_NAMESPACE=it-continuum

echo "Vault Configuration:"
echo "  Address: $VAULT_ADDR"
echo "  Namespace: $VAULT_NAMESPACE"
echo ""

# Check if already logged in
if ! vault token lookup &> /dev/null; then
    echo "🔐 Please authenticate with Vault..."
    echo ""
    vault login -method=oidc -path=oidc-admins role=namespace-admin
    echo ""
fi

echo "✅ Authenticated with Vault"
echo ""

# Prepare the vault path
VAULT_PATH="KVv2/it-continuum/prd/$APP_NAME"

echo "============================================================================"
echo "PUSHING SECRETS TO VAULT"
echo "============================================================================"
echo ""
echo "This will push the following environment variables:"
echo ""
echo "  1. NATSP_REACT_NVIDIA_API_KEY"
echo "  2. NATSP_REACT_DATAROBOT_API_KEY"
echo "  3. NATSP_REACT_ECI_CLIENT_ID"
echo "  4. NATSP_REACT_ECI_CLIENT_SECRET"
echo "  5. NATSP_REACT_POSTGRES_USER"
echo "  6. NATSP_REACT_POSTGRES_PASSWORD"
echo "  7. NATSP_REACT_POSTGRES_HOST"
echo "  8. NATSP_REACT_POSTGRES_PORT"
echo "  9. NATSP_REACT_POSTGRES_DB"
echo " 10. NATSP_REACT_POSTGRES_SCHEMA"
echo " 11. NATSP_REACT_MILVUS_URI"
echo " 12. NATSP_REACT_MILVUS_USER"
echo " 13. NATSP_REACT_MILVUS_PASSWORD"
echo " 14. NATSP_REACT_MILVUS_COLLECTION"
echo " 15. NATSP_REACT_MCP_USER_ID"
echo " 16. NATSP_REACT_MCP_ALLOW_DEFAULT_USER"
echo " 17. NATSP_REACT_MCP_REDIRECT_URI"
echo " 18. NATSP_REACT_MCP_SERVER_URL"
echo ""
echo "Path: $VAULT_PATH"
echo ""

read -p "Do you want to continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Aborted by user"
    exit 1
fi

echo ""
echo "Pushing secrets to vault..."
echo ""

# Check if the path already exists
if vault kv get "$VAULT_PATH" &> /dev/null; then
    echo "Path exists, using 'patch' to merge with existing secrets..."
    VAULT_CMD="patch"
else
    echo "Path does not exist, using 'put' to create new secrets..."
    VAULT_CMD="put"
fi

echo ""

# Push secrets to vault
vault kv "$VAULT_CMD" "$VAULT_PATH" \
  NATSP_REACT_NVIDIA_API_KEY="$NATSP_REACT_NVIDIA_API_KEY" \
  NATSP_REACT_DATAROBOT_API_KEY="$NATSP_REACT_DATAROBOT_API_KEY" \
  NATSP_REACT_ECI_CLIENT_ID="$NATSP_REACT_ECI_CLIENT_ID" \
  NATSP_REACT_ECI_CLIENT_SECRET="$NATSP_REACT_ECI_CLIENT_SECRET" \
  NATSP_REACT_POSTGRES_USER="$NATSP_REACT_POSTGRES_USER" \
  NATSP_REACT_POSTGRES_PASSWORD="$NATSP_REACT_POSTGRES_PASSWORD" \
  NATSP_REACT_POSTGRES_HOST="$NATSP_REACT_POSTGRES_HOST" \
  NATSP_REACT_POSTGRES_PORT="$NATSP_REACT_POSTGRES_PORT" \
  NATSP_REACT_POSTGRES_DB="$NATSP_REACT_POSTGRES_DB" \
  NATSP_REACT_POSTGRES_SCHEMA="$NATSP_REACT_POSTGRES_SCHEMA" \
  NATSP_REACT_MILVUS_URI="$NATSP_REACT_MILVUS_URI" \
  NATSP_REACT_MILVUS_USER="$NATSP_REACT_MILVUS_USER" \
  NATSP_REACT_MILVUS_PASSWORD="$NATSP_REACT_MILVUS_PASSWORD" \
  NATSP_REACT_MILVUS_COLLECTION="$NATSP_REACT_MILVUS_COLLECTION" \
  NATSP_REACT_MCP_USER_ID="$NATSP_REACT_MCP_USER_ID" \
  NATSP_REACT_MCP_ALLOW_DEFAULT_USER="$NATSP_REACT_MCP_ALLOW_DEFAULT_USER" \
  NATSP_REACT_MCP_REDIRECT_URI="$NATSP_REACT_MCP_REDIRECT_URI" \
  NATSP_REACT_MCP_SERVER_URL="$NATSP_REACT_MCP_SERVER_URL"

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================================"
    echo "✅ SUCCESS!"
    echo "============================================================================"
    echo ""
    echo "All secrets have been pushed to vault at:"
    echo "  $VAULT_PATH"
    echo ""
    echo "You can now use this vault path in your Astra deployment configuration."
    echo ""
    echo "To verify the secrets were saved correctly, run:"
    echo "  vault kv get $VAULT_PATH"
    echo ""
    echo "============================================================================"
else
    echo ""
    echo "❌ Failed to push secrets to vault!"
    exit 1
fi

