# SPDX-FileCopyrightText: Copyright (c) 2023-2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging
import os
import time
import jwt
import base64
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

import requests
from pydantic import BaseModel, Field

from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.builder.context import Context
from nat.runtime.user_metadata import RequestAttributes
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig
from nat.builder.framework_enum import LLMFrameworkEnum

logger = logging.getLogger(__name__)


class ECISearchToolConfig(FunctionBaseConfig, name="eci_search_tool"):
    """
    Enterprise Content Intelligence (ECI) search tool configuration.
    Searches internal NVIDIA content using natural language queries.
    """

    environment: str = Field(
        default="prod", description="Environment to use (dev, stg, prod)"
    )
    output_folder: str = Field(
        default="output_data", description="Folder to save JSON search results"
    )
    eci_client_id: str = Field(
        description="Client ID for ECI API authentication"
    )
    eci_client_secret: str = Field(
        description="Client secret for ECI API authentication"
    )


class ECISearchAPI:
    """Enterprise Content Intelligence API client."""

    ENVIRONMENT_MAP = {
        "dev": "https://ecs-enrichment-api-dev.nvidia.com",
        "stg": "https://enterprise-content-intelligence-stg.nvidia.com",
        "prod": "https://enterprise-content-intelligence.nvidia.com",
    }

    TOKEN_ENDPOINT_MAP = {
        "dev": "https://0ek1bxdw6fwpho5fzvsbonmmhhubotfodakxbpwmepm.stg.ssa.nvidia.com/token",
        "stg": "https://0ek1bxdw6fwpho5fzvsbonmmhhubotfodakxbpwmepm.stg.ssa.nvidia.com/token",
        "prod": "https://slcjppsefswu84b0uew-sqhfmcnjwgfj-l0lvdmcmvs.ssa.nvidia.com/token",
    }

    TOKEN_SCOPE = (
        "content:classify content:summarize content:search content:retrieve content:retrieve_metadata "
        "account:verify_access"
    )

    def __init__(self, config: ECISearchToolConfig):
        self.config = config
        self._cached_token: Optional[str] = None
        self._token_expiry: float = 0

    def get_auth_token(self) -> Optional[str]:
        """Retrieve and cache the service-to-service authentication token."""
        now = time.time()
        t0 = time.monotonic()

        if self._cached_token and now < self._token_expiry - 60:
            logger.debug(
                "ECI token: using cached token, expires_in=%ds",
                int(self._token_expiry - now),
            )
            return self._cached_token

        client_id = self.config.eci_client_id
        client_secret = self.config.eci_client_secret

        if client_id.startswith(('"', "'")) and client_id.endswith(('"', "'")):
            client_id = client_id[1:-1]
        if client_secret.startswith(('"', "'")) and client_secret.endswith(('"', "'")):
            client_secret = client_secret[1:-1]

        credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        token_endpoint = self.TOKEN_ENDPOINT_MAP.get(
            self.config.environment, self.TOKEN_ENDPOINT_MAP["prod"]
        )
        logger.debug(
            "ECI token: requesting new token from %s (client_id_prefix=%s)",
            token_endpoint,
            (client_id[:6] if client_id else None),
        )

        response = requests.post(
            token_endpoint,
            data={"grant_type": "client_credentials", "scope": self.TOKEN_SCOPE},
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            timeout=30,
        )
        response.raise_for_status()
        token_data = response.json()
        self._cached_token = token_data.get("access_token")
        self._token_expiry = now + token_data.get("expires_in", 3600)
        logger.debug(
            "ECI token: acquired in %.3fs, ttl=%ds",
            time.monotonic() - t0,
            int(token_data.get("expires_in", 3600)),
        )
        return self._cached_token

    def get_api_host(self) -> str:
        """Returns the API host based on the current environment."""
        return self.ENVIRONMENT_MAP.get(
            self.config.environment, self.ENVIRONMENT_MAP["prod"]
        )

    def make_api_request(self, endpoint: str, payload: Dict[str, Any], sso_token: Optional[str] = None) -> Dict:
        """Make an authenticated POST request to the API."""
        url = f"{self.get_api_host()}{endpoint}"
        ssa_token = self.get_auth_token()

        if sso_token:
            logger.info("Received SSO token from context")     
        else:
            raise ValueError("SSO token is not available. Please use a frontend with SSO authentication enabled.")

        t0 = time.monotonic()
        logger.debug("ECI request: POST %s payload_keys=%s", url, list(payload.keys()))
        headers = {
            "Authorization": f"Bearer {ssa_token}",
            "Content-Type": "application/json",
            "Nv-Actor-Token": sso_token,
            "Nv-Actor-Token-Type": "id_token",
            "Accept": "application/json",
        }
        response = requests.post(url, headers=headers, json=payload, timeout=180)
        if not response.ok:
            # Log helpful diagnostics without dumping full secrets
            logger.error(
                "ECI request failed: status=%s url=%s body_snippet=%s ssa_len=%s sso_len=%s",
                response.status_code,
                url,
                (
                    response.text[:200]
                    if isinstance(response.text, str)
                    else str(response.content)[:200]
                ),
                (len(ssa_token) if isinstance(ssa_token, str) else None),
                (len(sso_token) if isinstance(sso_token, str) else None),
            )
            response.raise_for_status()
        data = response.json()
        logger.debug(
            "ECI request: status=%s elapsed=%.3fs results_count=%s",
            response.status_code,
            time.monotonic() - t0,
            (
                len(data.get("results", []))
                if isinstance(data, dict) and isinstance(data.get("results"), list)
                else "n/a"
            ),
        )
        return data

    def search(self, query: str, sso_token: Optional[str] = None) -> Dict:
        """
        Calls the search API.

        Args:
            query (str): Natural language search query

        Returns:
            dict: Search results from ECI API
        """
        payload = {"query": query}
        return self.make_api_request("/v1/content/search", payload, sso_token)


def escape_markdown(text: str) -> str:
    """Escape markdown special characters in text."""
    if not isinstance(text, str):
        return str(text)
    return text.replace("|", "\\|").replace("\n", " ")


def format_search_results_markdown(response: Dict[str, Any]) -> str:
    """
    Format ECI search results as markdown table.

    Args:
        response (dict): ECI API response

    Returns:
        str: Formatted markdown table
    """
    results = response.get("results", []) if isinstance(response, dict) else []
    if not results:
        return (
            "No results found for your query.\n\n"
            "**Suggestions:**\n"
            "- Try different keywords or phrases\n"
            "- Use broader search terms\n"
            "- Check if the content exists in NVIDIA's internal systems\n"
            "- Verify your search query spelling"
        )

    headers = ["#", "Title", "Datasource", "Type", "Updated", "URL"]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for idx, item in enumerate(results, start=1):
        doc = (item or {}).get("document", {})
        title = item.get("title") or doc.get("title") or "(untitled)"
        url = item.get("url") or doc.get("url") or ""
        metadata = doc.get("metadata", {})
        datasource = metadata.get("datasource") or doc.get("datasource") or ""
        doc_type = doc.get("docType") or metadata.get("objectType") or ""
        updated = metadata.get("updateTime") or metadata.get("createTime") or ""

        title_disp = escape_markdown(title)
        if len(title_disp) > 80:
            title_disp = title_disp[:77] + "..."

        url_disp = f"[{title_disp}]({url})" if url else title_disp

        row = [
            str(idx),
            url_disp,
            escape_markdown(str(datasource)),
            escape_markdown(str(doc_type)),
            escape_markdown(str(updated)),
            escape_markdown(url),
        ]
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def save_json_results(response: Dict[str, Any], query: str, output_folder: str) -> str:
    """
    Save JSON results to output folder.

    Args:
        response (dict): ECI API response
        query (str): Original search query
        output_folder (str): Output folder path

    Returns:
        str: Path to saved file
    """
    # Create output folder if it doesn't exist
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_query = "".join(
        c for c in query if c.isalnum() or c in (" ", "-", "_")
    ).rstrip()
    safe_query = safe_query.replace(" ", "_")[:50]  # Limit length
    filename = f"eci_search_{safe_query}_{timestamp}.json"
    filepath = Path(output_folder) / filename

    # Save results with metadata
    output_data = {
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "results_count": len(response.get("results", [])),
        "response": response,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved ECI search results to: {filepath}")
    return str(filepath)


@register_function(
    config_type=ECISearchToolConfig, framework_wrappers=[LLMFrameworkEnum.LANGCHAIN]
)
async def eci_search_tool(config: ECISearchToolConfig, builder: Builder):
    """
    Enterprise Content Intelligence (ECI) search tool.

    Searches internal NVIDIA content using natural language queries and returns
    results in markdown format for frontend rendering. Also saves JSON results
    to the output folder.
    """

    class ECISearchInputSchema(BaseModel):
        query: str = Field(description="Natural language search query for ECI content")

    # Initialize ECI API client (raises early if env vars are missing)
    eci_api = ECISearchAPI(config)

    async def _response_fn(query: str) -> str:
        logger.info(f"Searching ECI for query: {query}")
        logger.debug("ECI tool: starting search flow")
        # Get SSO token from context
        context = Context.get()
        metadata: RequestAttributes = context.metadata
        sso_token = None
        if metadata and metadata.headers:
            auth_header = metadata.headers.get("authorization", "")
            sso_token = auth_header.split(" ")[1] if " " in auth_header else auth_header
        
        logger.info("SSO token at tool from context at registration")        
        

        # Sample Code for DL Check with Helios
        # try:
        #     helios_api_url = os.getenv("HELIOS_API_URL")
        #     helios_auth_token = os.getenv("HELIOS_AUTH_TOKEN")
        #     required_group = os.getenv("HELIOS_REQUIRED_GROUP")
        #
        #     if not helios_auth_token:
        #         logger.error("HELIOS_AUTH_TOKEN environment variable not set")
        #
        #     # Call Helios API to check user access
        #     headers = {"auth-token": helios_auth_token}
        #     params = {
        #         "filter[descendantUserLogin]": username,
        #         "filter[names]": required_group,
        #     }
        #
        #     response = requests.get(
        #         helios_api_url, headers=headers, params=params, timeout=10
        #     )
        #
        #     if response.status_code == 200:
        #         data = response.json()
        #         if (len(data.get("data", [])) == 1):
        #             logger.info(f"Is a member of DL")
        #         else:
        #             logger.info(f"Is not a member of DL")
        #     else:
        #         logger.error(f"Helios API returned status {response.status_code}")
        # except requests.RequestException as e:
        #     logger.error(f"Failed to call Helios API: {e}")
        # except Exception as e:
        #     logger.error(f"Unexpected error during token validation: {e}")

        response = eci_api.search(query, sso_token)
        logger.debug("ECI tool: search completed, formatting & saving")
        file_path = save_json_results(response, query, config.output_folder)
        abs_file_path = str(Path(file_path).resolve())
        results_count = len(response.get("results", []))
        header = (
            f"# ECI Search Results Saved in JSON File: {abs_file_path}\n\n"
            f"**Query:** {query}\n**Results:** {results_count} found\n\n"
        )
        logger.debug(
            "ECI tool: return markdown, results_count=%s file=%s",
            results_count,
            file_path,
        )
        return header + format_search_results_markdown(response)

    description = """Search NVIDIA internal content using the Enterprise Content Intelligence (ECI) API.
        Input: natural-language query to send to the ECI API.
        "Output: returns a markdown table to render in frontendand saves the results in a JSON file in output folder."""

    yield FunctionInfo.from_fn(
        _response_fn,
        input_schema=ECISearchInputSchema,
        description=description,
    )
    try:
        pass
    except GeneratorExit:
        logger.info("ECI search tool exited early!")
    finally:
        logger.info("Cleaning up ECI search tool.")
