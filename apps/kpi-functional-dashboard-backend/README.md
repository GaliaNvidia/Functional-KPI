# NAT React Agent Blueprint - Agentic Workflow (SQL + ECI + MCP)

A **NeMo Agent Toolkit (NAT)** application that 
1) Demonstrates how to build an AI agent with Text to SQL query capabilities. 
2) Demonstrates how to build agents requiring SSO authentication like NVIDIA ECI search tool.
3) Demonstrates how to integrate MCP (Model Context Protocol) tools from MaaS servers (Jira, GitLab, Confluence, etc.).

## Architecture

```
┌─────────────────┐           ┌──────────────────┐
│   Natural       │           │   Northwind      │
│   Language      │──────────▶│   Database       │
│   Queries       │           │   (SQLite/       │
└─────────────────┘           │    PostgreSQL)   │
        │                     │   + Vanna AI     │
        │                     └──────────────────┘
        ▼
┌────────────────────────────────────────────────────────────────┐
│                  NeMo Agent Toolkit (NAT)                      │
│     Conversational agent orchestrating tools in workflow       │
│  ┌─────────────────┐  ┌──────────┐  ┌──────────────────────┐   │
│  │ SQL Query &     │  │ ECI      │  │ MCP Tools (Jira,     │   │
│  │ Retrieve Tool   │  │ Search   │  │ GitLab, Confluence,  │   │
│  │                 │  │ Tool     │  │ Google Drive, etc.)  │   │
│  └─────────────────┘  └──────────┘  └──────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │   MaaS MCP Servers     │
                    │   (OAuth2 Protected)   │
                    └────────────────────────┘
```

## Configuration Options

This blueprint supports two deployment modes with separate configuration files:

### 📁 configs/config-local.yaml (Local Development)
- **Database**: SQLite (file-based, lightweight)
- **Vector Store**: ChromaDB (local, no external dependencies)
- **Best for**: Local testing, development, prototyping
- **Advantages**: Quick setup, no infrastructure dependencies

### 📁 configs/config-prod.yaml (Production Deployment)
- **Database**: PostgreSQL (IT-managed, scalable)
- **Vector Store**: Milvus (IT-managed, production-ready)
- **Best for**: Production deployments, enterprise environments
- **Advantages**: Scalable, managed infrastructure, multi-user support

## Quick Start
### Prerequisites

#### Basic Requirements
- Python 3.11+
- NVIDIA API key for using build.nvidia.com models
- Datarobot API key for using Astra's community models hosted in Datarobot
- ECI (Enterprise Content Intelligence) credentials for internal content search (think Glean)
- Access to MaaS MCP servers (Jira, GitLab, etc.) - OAuth2 authentication handled automatically on first use

#### Additional Requirements for Production (config-prod.yaml)
- PostgreSQL database credentials (contact IT for access)
- Milvus vector database credentials (request from database platform team)
  ```bash
  # Get Milvus credentials using:
  ~/milvus-cli show dev <your-cluster-name>
  ```

### Local Development Setup

1. **Install the package**:
   
   The package requires NAT 1.3.0rc5 or higher for MCP support (pre-release version):
   ```bash
   # Using pip
   pip install -e .
   
   # OR using uv (recommended for faster installation)
   uv pip install -e .
   ```

2. **Set up the Northwind database**:
   
   See the [SQL Retrieval Tool](#the-sql-retrieval-tool) section below for complete database setup instructions (SQLite for development, PostgreSQL for production).

3. **Configure environment variables**:

   Copy the environment template and configure your credentials:
   ```bash
   cp env_template.sh env.sh
   ```

   Edit the env.sh file with your actual credentials:

   Minimum number of environment variables required to run this workflow:
   * NATSP_REACT_NVIDIA_API_KEY or NATSP_REACT_DATAROBOT_API_KEY for LLMs
   * NATSP_REACT_ECI_CLIENT_ID for ECI tool
   * NATSP_REACT_ECI_CLIENT_SECRET for ECI tool

   other variables related to Milvus, Postgres SQL etc. can be exported as needed.

   > To obtain your Enterprise Content Intelligence (ECI) credentials, visit the [ECI documentation](https://enterprise-content-intelligence.nvidia.com/#/) for setup instructions.   

   Then source the environment:
   ```bash
   source env.sh
   ```

4. **Configure LLM and Embedder Endpoints**:

   When using DataRobot deployments with OpenAI-compatible endpoints, use the following base URL patterns:

   **For LLMs (Chat Completions)**:
   ```yaml
   llms:
     my_llm:
       _type: openai
       base_url: https://datarobot.prd.astra.nvidia.com/api/v2/deployments/<DEPLOYMENT_ID>/v1
       model_name: "your-model-name"
       api_key: ${NATSP_REACT_DATAROBOT_API_KEY}
   ```
   
   **For Embeddings**:
   ```yaml
   embedders:
     my_embedder:
       _type: openai
       base_url: https://datarobot.prd.astra.nvidia.com/api/v2/deployments/<DEPLOYMENT_ID>/directAccess/nim/v1
       model_name: "your-embedding-model-name"
       api_key: ${NATSP_REACT_DATAROBOT_API_KEY}
   ```

   > **Key Difference**: 
   > - **LLMs**: Use `{deployment_url}/v1` suffix
   > - **Embeddings**: Use `{deployment_url}/directAccess/nim/v1` suffix
   >
   > The OpenAI Python library will automatically append `/chat/completions` for LLMs and `/embeddings` for embeddings to these base URLs.

6. **Start the NAT agent**:
   
   For local development (SQLite + ChromaDB):
   ```bash
   nat serve --config_file=configs/config-local.yaml
   ```
   
   For production (PostgreSQL + Milvus):
   ```bash
   nat serve --config_file=configs/config-prod.yaml
   ```
   
   > **Note**: The original `config-react.yaml` is deprecated. Use `config-local.yaml` for local development or `config-prod.yaml` for production deployments. You can also run config-prod.yaml file from your local machine as long as the right credentials are exported in the env.sh file.

7. **Interact with the agent**:
  
  If you deployed the workflow locally, then:
  Option 1: Clone the [NeMo Agent Toolkit UI](https://github.com/NVIDIA/NeMo-Agent-Toolkit-UI) repo and spin it up in your local machine. Follow the instructions in the repo to interact with your workflow
  Option 2: Create a copy of Astra's [Enterprise Chat UI with Auth](https://console.astra.nvidia.com/blueprints) blueprint, clone it locally, spin it up and follow the same instructions as 1)
  
  If you deployed this workflow in Astra, then:
  Use the already deployed [Enterprise Chat UI](https://chat-frontend.stg.astra.nvidia.com/home) to test your workflow. Note: This deployment cannot take `localhost` endpoints.

## The SQL Retrieval Tool

### Overview
**Type**: `generate_sql_query_and_retrieve_tool`

This tool demonstrates the core pattern for NAT tools:
- Takes natural language input
- Uses Vanna AI to convert to SQL
- Executes against the database (SQLite or PostgreSQL)
- Returns structured results


### Database and Vector Store Setup

The SQL retrieval tool supports flexible configurations for both databases and vector stores:

**Database Options:**
- **SQLite** (local development) - Use with `config-local.yaml`
- **PostgreSQL** (production) - Use with `config-prod.yaml`

**Vector Store Options:**
- **ChromaDB** (local development) - Use with `config-local.yaml`
- **Milvus** (IT-managed production) - Use with `config-prod.yaml`

The system automatically uses the appropriate database and vector store based on your configuration file.

---

#### Local Development Setup (config-local.yaml)

**What you get:**
- SQLite database (local file)
- ChromaDB vector store (local directory)
- No external infrastructure needed

**Setup Steps:**

1. Set up the SQLite database:
   ```bash
   python setup_database.py
   ```

2. Use the local configuration:
   ```bash
   nat serve --config_file=configs/config-local.yaml
   ```

The `config-local.yaml` file is already configured with:
- `sqlite_db_path: "database/northwind.db"`
- `vector_store_path: "database"`
- `use_milvus: false` (uses ChromaDB)
- `vanna_training_data_path: "vanna_sqlite_training_data.yaml"`

---

#### Production Setup (config-prod.yaml)

**What you need:**
- PostgreSQL database credentials
- Milvus vector database credentials
- Production-grade infrastructure

**Setup Steps:**

##### Step 1: Request PostgreSQL Database

Run the following command for instructions:
```bash
python setup_database.py --postgres-help
```

##### Step 2: Request Milvus Vector Database

Milvus DB request [details](https://console-stg.astra.nvidia.com/vectordbs)

You'll receive:
- **URI**: `https://milvus-astra-users-dev.db.nvw.nvidia.com`
- **Username**: e.g., `developer`, `owner`, `curator`, `viewer`
- **Password**: Your access password
- **Collection Name**: Configurable via `NATSP_REACT_MILVUS_COLLECTION` (default: `vanna_northwind_embeddings`)
  - The collection will be created automatically on first use if it doesn't exist

> **⚠️ Important - Role Permissions:**
> 
> | Role | Create Collections | Write | Read | Delete | Recommended For |
> |------|-------------------|-------|------|--------|-----------------|
> | **`owner`** | ✅ | ✅ | ✅ | ✅ | Initial setup, full admin |
> | **`curator`** | ✅ | ✅ | ✅ | ✅ | Initial setup, production use |
> | **`developer`** | ❌ | ✅* | ✅ | ❓ | Runtime only (after setup) |
> | **`viewer`** | ❌ | ❌ | ✅ | ❌ | Read-only access |
> 
> *Can write to existing collections only
> 
> **For first-time setup**, use either **`owner`** or **`curator`** role to allow automatic collection creation.
> After initial setup, you can use **`developer`** role for runtime operations.

##### Step 3: Set Up PostgreSQL Database

Once you receive PostgreSQL credentials, export them as environment variables

```bash
export NATSP_REACT_POSTGRES_USER=
export NATSP_REACT_POSTGRES_PASSWORD=
export NATSP_REACT_POSTGRES_HOST=              # e.g., wfo-astra-prd-rw.db.nvidia.com
export NATSP_REACT_POSTGRES_PORT=              # Default PostgreSQL port
export NATSP_REACT_POSTGRES_DB=                # e.g., astra_blueprints
export NATSP_REACT_POSTGRES_SCHEMA=public      # e.g. northwind or simply leave it as 'public'
```

and run the setup database script with PostgresSQL connection string to create the Northwind database in Postgres.

```bash
python setup_database.py --postgres \
    --connection-string "postgresql://$NATSP_REACT_POSTGRES_USER:$NATSP_REACT_POSTGRES_PASSWORD@$NATSP_REACT_POSTGRES_HOST:5432/$NATSP_REACT_POSTGRES_DB"
```

##### Step 4: Configure Environment Variables

Edit `env.sh` and add your PostgreSQL and Milvus credentials:
```bash
# PostgreSQL Database Configuration (for production)
export NATSP_REACT_POSTGRES_USER="your_username"
export NATSP_REACT_POSTGRES_PASSWORD="your_password"
export NATSP_REACT_POSTGRES_HOST="wfo-astra-prd-rw.db.nvidia.com"
export NATSP_REACT_POSTGRES_PORT=5432
export NATSP_REACT_POSTGRES_DB="astra_blueprints"
export NATSP_REACT_POSTGRES_SCHEMA="public"

# Milvus Vector Database Configuration (for production)
export NATSP_REACT_MILVUS_URI="https://milvus-astra-users-dev.db.nvw.nvidia.com"
export NATSP_REACT_MILVUS_USER="curator"  # Use 'owner' or 'curator' for initial setup
export NATSP_REACT_MILVUS_PASSWORD="your_milvus_password"
export NATSP_REACT_MILVUS_COLLECTION="vanna_northwind_embeddings"  # Collection name for embeddings
```

Then source your environment:
```bash
source env.sh
```

##### Step 5: Run with Production Configuration

```bash
nat serve --config_file=configs/config-prod.yaml
```

The `config-prod.yaml` file is already configured with:
- PostgreSQL connection using environment variables
- Milvus vector store with `use_milvus: true`
- Production-ready settings
- `vanna_training_data_path: "vanna_postgres_training_data.yaml"`

### Vanna Training Data Files: SQLite vs PostgreSQL

This blueprint includes **two separate training data files** for Vanna AI:

#### `vanna_sqlite_training_data.yaml`
- **Use for**: Local development with SQLite database
- **SQL Syntax**: Standard SQLite syntax
- **Identifiers**: Unquoted or single-quoted identifiers
- **Example**: `SELECT * FROM Customers WHERE Country = 'Germany'`

#### `vanna_postgres_training_data.yaml`
- **Use for**: Production deployment with PostgreSQL database  
- **SQL Syntax**: PostgreSQL-specific syntax
- **Identifiers**: **All table and column names must be double-quoted** (case-sensitive)
- **Example**: `SELECT * FROM "Customers" WHERE "Country" = 'Germany'`

> **Note:** PostgreSQL and SQLite differ significantly in several aspects of SQL syntax. PostgreSQL is case-sensitive and requires double quotes around table and column names, whereas SQLite does not. Their data type systems also differ: for example, SQLite uses `BLOB` for binary data, while PostgreSQL uses `BYTEA` and prefers `NUMERIC` instead of `REAL`. Additionally, date functions have different names and behaviors, with SQLite using functions like `date()` and `strftime()`, while PostgreSQL uses `TO_CHAR()`, `DATE_TRUNC()`, and `EXTRACT()`. Be sure to use the correct training data file and syntax for your chosen database to avoid SQL errors.

**Using the wrong training file will cause SQL syntax errors!** The Vanna AI model learns SQL patterns from training examples, so it must be trained with the correct syntax for your database type.

### Customize SQL retriever tool for Your Database

To adapt this tool for your own database:

1. **Follow the setup instructions** in the [Database Setup](#database-setup) section above based on your database type (SQLite or PostgreSQL)
2. **Update the training data file** (`vanna_sqlite_training_data.yaml` or `vanna_postgres_training_data.yaml`) to reflect your schema:
   - Add your table definitions
   - Include sample questions and corresponding SQL queries
   - Document important joins and relationships
3. **Configure database connection** in `configs/config-react.yaml` as shown in the Database Setup section
4. **Optional**: Update `vector_store_path` to customize where embeddings are stored

> **Note**: You do not need to modify `src/nat_react_agent_blueprint/vanna_manager.py` or `src/nat_react_agent_blueprint/vanna_util.py`.

## The ECI Search Tool

### Overview
**Type**: `eci_search_tool`

This tool demonstrates how to integrate IT managed internally hosted APIs with NAT. It searches NVIDIA internal content using [Enterprise Content Intelligence (ECI)](https://enterprise-content-intelligence.nvidia.com/) using SSA authentication method.

### Example Usage
- "Find NPN training courses"
- "Search for GPU architecture documentation"
- "Look up NVIDIA partner program policies"

### Required Environment Variables

The ECI search tool requires the following environment variables to be set:

| Variable | Description | How to Obtain |
|----------|-------------|---------------|
| `NATSP_REACT_ECI_CLIENT_ID` | Client ID for ECI API authentication | Contact your NVIDIA IT administrator or ECI team |
| `NATSP_REACT_ECI_CLIENT_SECRET` | Client secret for ECI API authentication | Contact your NVIDIA IT administrator or ECI team |

Simply update them in your `env.sh` file, export it and rerun your workflow.

> Note: This tool requires you to interact with a frontend that has SSO authentication built in. Either deploy this [Enterprise Chat UI with Auth](https://console.astra.nvidia.com/blueprints) locally, or use a deployed version of this [here](https://chat-frontend.stg.astra.nvidia.com/home)

## The MaaS MCP Tool

### Overview
This tool demonstrates using NAT to connect to IT-Managed MCP Servers called MaaS (MCP as a Service)[https://ipp-safety-tools.gitlab-master-pages.nvidia.com/giza-llm-tools/giza_ai/] that provide various MCP server to various enterprise tools used internally through a standardized protocol. This blueprint supports providing any of the available MCP servers hosted as MaaS like GitLab, Confluence, Google Drive, SharePoint, OneDrive, and more.

**For complete MCP setup documentation, see:** [NAT MCP Quickstart Guide](https://ipp-safety-tools.gitlab-master-pages.nvidia.com/giza-llm-tools/giza_ai/docs/tutorial/nat-quickstart)

### Key Features
- **OAuth2 Authentication**: Secure authentication with token caching
- **Multi-Server Support**: Connect to multiple MaaS servers simultaneously
- **Single & Multi-User Modes**: Works in both CLI (single user) and server (multi-user) deployments

### Configuration

```yaml
function_groups:
  maas_mcp_tool:
    _type: mcp_client
    server:
      transport: streamable-http
      url: ${NATSP_REACT_MCP_SERVER_URL}
      auth_provider: maas_mcp_tool_auth

authentication:
  maas_mcp_tool_auth:
    _type: mcp_oauth2
    server_url: ${NATSP_REACT_MCP_SERVER_URL}
    redirect_uri: ${NATSP_REACT_MCP_REDIRECT_URI}
    default_user_id: ${NATSP_REACT_MCP_USER_ID}
    allow_default_user_id_for_tool_calls: ${NATSP_REACT_MCP_ALLOW_DEFAULT_USER}
```

### Environment Variables

Set these in `env.sh` (see `env_template.sh` for details):

| Variable | Description | Required |
|----------|-------------|----------|
| `NATSP_REACT_MCP_SERVER_URL` | MaaS MCP server URL to connect to | **Yes** |
| `NATSP_REACT_MCP_USER_ID` | User ID for caching credentials | Optional |
| `NATSP_REACT_MCP_ALLOW_DEFAULT_USER` | `true` for CLI, `false` for server mode | Optional |
| `NATSP_REACT_MCP_REDIRECT_URI` | OAuth callback URL | Optional |

### Available MaaS MCP Servers

Set `NATSP_REACT_MCP_SERVER_URL` to one of these:

| Server | URL | Description |
|--------|-----|-------------|
| **Jira** | `https://nvaihub.nvidia.com/maas/jira/mcp/` | Jira ticket management |
| **GitLab** | `https://nvaihub.nvidia.com/maas/gitlab/mcp/` | GitLab project management |
| **Confluence** | `https://nvaihub.nvidia.com/maas/confluence/mcp/` | Documentation access |
| **Google Drive** | `https://nvaihub.nvidia.com/maas/gdrive/mcp/` | File access |
| **SharePoint** | `https://nvaihub.nvidia.com/maas/sharepoint/mcp/` | Document management |
| **OneDrive** | `https://nvaihub.nvidia.com/maas/onedrive/mcp/` | File access |

### Example Usage

Depending on which MaaS server you configure:

**Jira Examples**:
- "What is jira ticket AIQ-1935 about?"
- "List all open tickets assigned to me"

**GitLab Examples**:
- "Show me recent merge requests in my project"
- "What are the open issues in the repository?"

> Note: On first use, a browser window will open for OAuth2 authentication.

## Adding New Tools to NAT

Follow these three steps to add any new tool to your NAT application:

### Step 1: Create a New Tool Python File

Create a new Python file in `src/nat_react_agent_blueprint/` (e.g., `my_new_tool.py`):

```python
from typing import Any, Dict, AsyncGenerator
from pydantic import BaseModel, Field

class MyNewToolConfig(BaseModel):
    """Configuration for your new tool"""
    parameter1: str = Field(description="Description of parameter1")
    parameter2: int = Field(default=10, description="Description of parameter2")

class MyNewToolInput(BaseModel):
    """Input schema for your tool"""
    query: str = Field(description="The input query or request")

async def my_new_tool(
    config: MyNewToolConfig,
    input_data: MyNewToolInput
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Your tool implementation

    Args:
        config: Tool configuration
        input_data: Input from the user/agent

    Yields:
        Dict containing results, status updates, or intermediate data
    """
    # Your tool logic here
    result = f"Processing: {input_data.query}"

    yield {
        "status": "processing",
        "message": "Starting work..."
    }

    # Do your actual work here
    final_result = {"result": result, "parameter1": config.parameter1}

    yield {
        "status": "completed",
        "data": final_result
    }
```

### Step 2: Import in Register File

Add your tool import to `src/nat_react_agent_blueprint/register.py`:

```python
# pylint: disable=unused-import
# flake8: noqa

# Import any tools which need to be automatically registered here
from . import generate_sql_query_and_retrieve_tool
from . import my_new_tool  # Add this line
```

### Step 3: Add to Config File

Update your `configs/config-react.yml` to include the new tool:

```yaml
functions:
  sql_retriever:
    _type: generate_sql_query_and_retrieve_tool
    llm_name: sql_llm
    embedding_name: vanna_embedder
    vector_store_path: "database"
    db_path: "database/northwind.db"
    output_folder: "output_data"
    vanna_training_data_path: "vanna_training_data.yaml"

  # Add your new tool here
  my_new_tool:
    _type: my_new_tool
    parameter1: "example_value"
    parameter2: 20

workflow:
  _type: react_agent
  llm_name: react_llm
  max_iterations: 20
  max_retries: 2
  tool_names: [
    sql_retriever,
    my_new_tool  # Add to tool names
  ]
```

## Running NAT Eval workflow

Nemo Agent Toolkit has evaluation built in, blueprint provides a sample
eval set in `eval_data/sample_eval_set.json` which is also specified in `config-*.yaml` files in.

You can test your workflow against all the evaluation queries by running

```bash 
nat eval --config_file=configs/config-react.yml 
```

in your local machine.

You can modify the Custom evaluator, evaluation prompt or the dataset according to your workflow's needs.

## Deployment on Astra

- The blueprint comes with its own CI/CD pipeline that automatically packages your NAT workflow into a docker container.
- Simply modify the workflow, change dockerfile if necessary, commit and push. 
- Look for "chore(main):release" job in your Gitlab pipelines to see the name of the docker image that got created after every commit.
- Use [patch], [minor], [major] headers in your commit to bump version (in `version.py`) file by 0.0.1, 0.1.0 and 1.0.0 respectively
- Please try to use NVIDIA Vault to store environment variables required for your worklow instead of providing them directly in the Astra deployment. This is to avoid your environment variables to be visible to anyone with the access to the deployment. 

More instructions on how to inject environment variables into Astra here

- [Vault setup Astra docs](https://docs.google.com/document/d/1Q_R9hnpOIh8CceGctuucxSlxpfIXBxcTnu5VKMiqDhc/edit?tab=t.0#bookmark=id.x4frkbrulsvj)
- [Vault CLI installation and adding variables](https://gitlab-master.nvidia.com/kaizen/services/vault/docs/-/tree/main/vault-agent).

Once you upload your environment variables simply specify your vault path in the deployment under "Vault Configuration":

![NAT React Agent blueprint Architecture](./imgs/env_vault.png)

### Using the Automated Vault Push Script

This blueprint includes a convenient script (`push_to_vault.sh`) that automatically pushes all required environment variables to NVIDIA Vault.

**Step 1: Install NVIDIA Vault CLI** (if not already installed)

```bash
curl https://urm.nvidia.com/artifactory/sw-kaizen-data-generic/com/nvidia/vault/vault-agent/2.4.4/nvault_agent_v2.4.4_darwin_universal.zip -o vault.zip
unzip vault.zip && sudo mv vault /usr/local/bin/ && chmod 755 /usr/local/bin/vault
```

**Step 2: Configure your environment variables**

Edit `env.sh` with your credentials (API keys, database connections, etc.)

**Step 3: Run the vault push script**

```bash
# Push with default app name (nat-react-agent-blueprint)
./push_to_vault.sh

# Or specify a custom app name
./push_to_vault.sh my-custom-app-name
```

The script will:
- Authenticate with NVIDIA Vault (opens browser for SSO)
- Push all 18 environment variables from `env.sh` to vault
- Create the vault path: `it-continuum/prd/<app-name>`

**Step 4: Use in Astra Deployment**

In your Astra deployment configuration, specify the vault path:
- **Vault Path**: `it-continuum/prd/nat-react-agent-blueprint` (or your custom app name)

The script automatically pushes these variables:
- API Keys (NVIDIA, DataRobot, ECI)
- PostgreSQL connection details
- Milvus vector database configuration
- MCP tool settings

**Manual Method** (if you prefer)

```bash
# Authenticate
export VAULT_ADDR=https://prod.internal.vault.nvidia.com
export VAULT_NAMESPACE=it-continuum
vault login -method=oidc -path=oidc-admins role=namespace-admin

# Add secrets manually
vault kv put KVv2/it-continuum/prd/<your-app-name> \
  NATSP_REACT_NVIDIA_API_KEY="your-nvidia-key" \
  NATSP_REACT_DATAROBOT_API_KEY="your-datarobot-key" \
  # ... add all other variables
```


## Learning Resources

### NeMo Agent Toolkit
- [NAT Documentation](https://docs.nvidia.com/nemo-agent-toolkit/)
- [NAT MCP Quickstart Guide](https://ipp-safety-tools.gitlab-master-pages.nvidia.com/giza-llm-tools/giza_ai/docs/tutorial/nat-quickstart) - Complete MCP setup guide
- [ECI Documentation](https://enterprise-content-intelligence.nvidia.com/)
- [Vanna Documentation](https://vanna.ai/docs/)

## Future direction
- Packaging an Astra NAT workflow as a MCP server to connect with your Cursor.
- DL based authentication at workflow level.

## Contributing

Please contact Vineeth Kalluru or Ashok Marannan to contribute to this blueprint.

## License

Apache 2.0 License - see the main repository for details.
