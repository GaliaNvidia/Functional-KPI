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

"""
VannaManager - A simplified manager for Vanna instances
"""

import os
import logging
import threading
import hashlib
from typing import Dict, Union
from .vanna_util import initVanna
from .vanna_nim import NIMVanna, NVIDIAEmbeddingFunction
from .vanna_openai import OpenAIVanna, OpenAIEmbeddingFunction
from .vanna_milvus import (
    NIMVannaMilvus,
    OpenAIVannaMilvus,
    MilvusNVIDIAEmbeddingFunction,
    MilvusOpenAIEmbeddingFunction,
)

logger = logging.getLogger(__name__)


class VannaManager:
    """
    A simplified singleton manager for Vanna instances.

    Key features:
    - Singleton pattern to ensure only one instance per configuration
    - Thread-safe operations
    - Simple instance management
    """

    _instances: Dict[str, "VannaManager"] = {}
    _lock = threading.Lock()

    def __new__(cls, config_key: str):
        """Ensure singleton pattern per configuration"""
        with cls._lock:
            if config_key not in cls._instances:
                logger.debug(
                    f"VannaManager: Creating new singleton instance for config: {config_key}"
                )
                cls._instances[config_key] = super().__new__(cls)
                cls._instances[config_key]._initialized = False
            else:
                logger.debug(
                    f"VannaManager: Returning existing singleton instance for config: {config_key}"
                )
            return cls._instances[config_key]

    def __init__(
        self,
        config_key: str,
        vanna_llm_config=None,
        vanna_embedder_config=None,
        vector_store_path: str = None,
        sqlite_db_path: str = None,
        training_data_path: str = None,
        postgres_config: dict = None,
        # Milvus configuration
        milvus_config: dict = None,
        use_milvus: bool = False,
    ):
        """
        Initialize the VannaManager and create Vanna instance immediately if all config is provided.
        
        Note: Prefer using the create_with_config() class method for clearer configuration.
        """
        if hasattr(self, "_initialized") and self._initialized:
            return

        self.config_key = config_key
        self.lock = threading.Lock()

        # Store configuration
        self.vanna_llm_config = vanna_llm_config
        self.vanna_embedder_config = vanna_embedder_config
        self.vector_store_path = vector_store_path
        self.sqlite_db_path = sqlite_db_path
        self.training_data_path = training_data_path
        self.postgres_config = postgres_config
        self.milvus_config = milvus_config
        self.use_milvus = use_milvus

        # Create and initialize Vanna instance immediately if all required config is provided
        self.vanna_instance = None
        has_db_config = sqlite_db_path or postgres_config
        has_vector_config = (vector_store_path and not use_milvus) or (milvus_config and use_milvus)
        if all([vanna_llm_config, vanna_embedder_config, has_vector_config, has_db_config]):
            logger.debug(
                "VannaManager: Initializing with immediate Vanna instance creation"
            )
            self.vanna_instance = self._create_instance()
        else:
            if any([vanna_llm_config, vanna_embedder_config, vector_store_path, has_db_config]):
                logger.debug(
                    "VannaManager: Partial configuration provided, Vanna instance will be created later"
                )
            else:
                logger.debug(
                    "VannaManager: No configuration provided, Vanna instance will be created later"
                )

        self._initialized = True
        logger.debug(f"VannaManager initialized for config: {config_key}")

    def get_instance(
        self,
        vanna_llm_config=None,
        vanna_embedder_config=None,
        vector_store_path: str = None,
        sqlite_db_path: str = None,
        training_data_path: str = None,
        postgres_config: dict = None,
        milvus_config: dict = None,
        use_milvus: bool = False,
    ) -> Union[NIMVanna, OpenAIVanna, NIMVannaMilvus, OpenAIVannaMilvus]:
        """
        Get the Vanna instance. If not created during init, create it now with provided parameters.
        
        Note: Prefer using the create_with_config() class method for clearer configuration.
        """
        with self.lock:
            if self.vanna_instance is None:
                logger.debug(
                    "VannaManager: No instance created during init, creating now..."
                )

                # Update configuration with provided parameters
                self.vanna_llm_config = vanna_llm_config or self.vanna_llm_config
                self.vanna_embedder_config = (
                    vanna_embedder_config or self.vanna_embedder_config
                )
                self.vector_store_path = vector_store_path or self.vector_store_path
                self.sqlite_db_path = sqlite_db_path or self.sqlite_db_path
                self.postgres_config = postgres_config or self.postgres_config
                self.training_data_path = training_data_path or self.training_data_path
                self.milvus_config = milvus_config or self.milvus_config
                self.use_milvus = use_milvus or self.use_milvus

                has_db_config = self.sqlite_db_path or self.postgres_config
                has_vector_config = (self.vector_store_path and not self.use_milvus) or (self.milvus_config and self.use_milvus)
                if all(
                    [
                        self.vanna_llm_config,
                        self.vanna_embedder_config,
                        has_vector_config,
                        has_db_config,
                    ]
                ):
                    self.vanna_instance = self._create_instance()
                else:
                    raise RuntimeError(
                        "VannaManager: Missing required configuration parameters"
                    )
            else:
                logger.debug(
                    f"VannaManager: Returning pre-initialized Vanna instance (ID: {id(self.vanna_instance)})"
                )

                # Show vector store status for pre-initialized instances
                if not self.use_milvus:
                    try:
                        if os.path.exists(self.vector_store_path):
                            list_of_folders = [
                                d
                                for d in os.listdir(self.vector_store_path)
                                if os.path.isdir(os.path.join(self.vector_store_path, d))
                            ]
                            logger.debug(
                                f"VannaManager: Vector store contains {len(list_of_folders)} collections/folders"
                            )
                            if list_of_folders:
                                logger.debug(
                                    f"VannaManager: Vector store folders: {list_of_folders}"
                                )
                        else:
                            logger.debug(
                                "VannaManager: Vector store directory does not exist"
                            )
                    except Exception as e:
                        logger.warning(
                            f"VannaManager: Could not check vector store status: {e}"
                        )
                else:
                    logger.debug("VannaManager: Using Milvus vector store")

            return self.vanna_instance

    def _create_instance(self) -> Union[NIMVanna, OpenAIVanna, NIMVannaMilvus, OpenAIVannaMilvus]:
        """
        Create a new Vanna instance using the stored configuration.
        Dynamically selects between NIMVanna and OpenAIVanna based on config types.
        Supports both ChromaDB (local) and Milvus (IT-managed) vector stores.
        Auto-detects database type (SQLite vs PostgreSQL) from connection string.
        """
        logger.info(f"VannaManager: Creating instance for {self.config_key}")
        
        # Log vector store configuration
        if self.use_milvus:
            logger.info("VannaManager: Using Milvus vector store")
            if self.milvus_config:
                logger.debug(f"VannaManager: Milvus URI: {self.milvus_config.get('uri', 'Not set')}")
                logger.debug(f"VannaManager: Milvus collection: {self.milvus_config.get('collection_name', 'vanna_embeddings')}")
        else:
            logger.info("VannaManager: Using ChromaDB vector store")
            logger.debug(f"VannaManager: Vector store path: {self.vector_store_path}")
        
        # Log database configuration
        if hasattr(self, 'sqlite_db_path') and self.sqlite_db_path:
            logger.debug(f"VannaManager: SQLite database: {self.sqlite_db_path}")
        elif hasattr(self, 'postgres_config') and self.postgres_config:
            logger.debug(f"VannaManager: PostgreSQL database: {self.postgres_config.get('host')}/{self.postgres_config.get('dbname')}")
        logger.debug(f"VannaManager: Training data path: {self.training_data_path}")

        # Detect LLM type from config
        llm_type = getattr(self.vanna_llm_config, "type", "nim").lower()
        embedder_type = getattr(self.vanna_embedder_config, "type", "nim").lower()
        
        logger.info(f"VannaManager: Detected LLM type: {llm_type}")
        logger.info(f"VannaManager: Detected Embedder type: {embedder_type}")
        
        embedding_function = None

        # Select appropriate embedding function based on embedder type and vector store
        if self.use_milvus:
            # Milvus embedding functions
            if embedder_type == "openai":
                logger.debug("VannaManager: Using Milvus OpenAI embedding function")
                embedding_function = MilvusOpenAIEmbeddingFunction(
                    api_key=self.vanna_embedder_config.api_key,
                    model=self.vanna_embedder_config.model_name,
                    base_url=self.vanna_embedder_config.base_url,
                )
            elif embedder_type == "nim":
                logger.debug("VannaManager: Using Milvus NVIDIA embedding function")
                embedding_function = MilvusNVIDIAEmbeddingFunction(
                    api_key=self.vanna_embedder_config.api_key,
                    model=self.vanna_embedder_config.model_name,
                )            
            else:
                raise ValueError(
                    f"VannaManager: Unsupported embedder type for Milvus: {embedder_type}. "
                    f"Supported types: 'nim', 'openai'"
                )
        else:
            # ChromaDB embedding functions
            if embedder_type == "openai":
                logger.debug("VannaManager: Using ChromaDB OpenAI embedding function")
                embedding_function = OpenAIEmbeddingFunction(
                    api_key=self.vanna_embedder_config.api_key,
                    model=self.vanna_embedder_config.model_name,
                    base_url=self.vanna_embedder_config.base_url,
                )
            elif embedder_type == "nim":
                logger.debug("VannaManager: Using ChromaDB NVIDIA embedding function")
                embedding_function = NVIDIAEmbeddingFunction(
                    api_key=self.vanna_embedder_config.api_key,
                    model=self.vanna_embedder_config.model_name,
                )            
            else:
                raise ValueError(
                    f"VannaManager: Unsupported embedder type for ChromaDB: {embedder_type}. "
                    f"Supported types: 'nim', 'openai'"
                )
            
        vn_instance = None
        
        # Configure vector store
        if self.use_milvus:
            # Milvus configuration
            vector_config = {
                "uri": self.milvus_config.get("uri"),
                "user": self.milvus_config.get("user"),
                "password": self.milvus_config.get("password"),
                "collection_name": self.milvus_config.get("collection_name", "vanna_embeddings"),
                "embedding_function": embedding_function,
            }
        else:
            # ChromaDB configuration
            vector_config = {
                "client": "persistent",
                "path": self.vector_store_path,
                "embedding_function": embedding_function,
            }
        
        llm_config = {
            "api_key": self.vanna_llm_config.api_key,
            "model": self.vanna_llm_config.model_name,
            "base_url": self.vanna_llm_config.base_url,
        }

        # Select appropriate Vanna class based on LLM type and vector store
        if self.use_milvus:
            # Milvus-based Vanna classes
            if llm_type == "openai":
                logger.debug("VannaManager: Creating OpenAIVannaMilvus instance")
                vn_instance = OpenAIVannaMilvus(
                    VectorConfig=vector_config,
                    LLMConfig=llm_config,
                )
            elif llm_type == "nim":
                logger.debug("VannaManager: Creating NIMVannaMilvus instance")
                vn_instance = NIMVannaMilvus(
                    VectorConfig=vector_config,
                    LLMConfig=llm_config,
                )
            else:
                raise ValueError(
                    f"VannaManager: Unsupported LLM type for Milvus: {llm_type}. "
                    f"Supported types: 'nim', 'openai'"
                )
        else:
            # ChromaDB-based Vanna classes
            if llm_type == "openai":
                logger.debug("VannaManager: Creating OpenAIVanna instance")
                vn_instance = OpenAIVanna(
                    VectorConfig=vector_config,
                    LLMConfig=llm_config,
                )
            elif llm_type == "nim":
                logger.debug("VannaManager: Creating NIMVanna instance")
                vn_instance = NIMVanna(
                    VectorConfig=vector_config,
                    LLMConfig=llm_config,
                )
            else:
                raise ValueError(
                    f"VannaManager: Unsupported LLM type for ChromaDB: {llm_type}. "
                    f"Supported types: 'nim', 'openai'"
                )

        # Connect to database - determine type from available config
        # If we have postgres_config, we know it's PostgreSQL
        if hasattr(self, 'postgres_config') and self.postgres_config:
            db_type = "postgresql"
            logger.info(f"VannaManager: Using PostgreSQL (from individual config fields)")
        elif hasattr(self, 'sqlite_db_path') and self.sqlite_db_path:
            db_type = "sqlite"
            logger.info(f"VannaManager: Using SQLite database at: {self.sqlite_db_path}")
        else:
            raise ValueError("No database configuration found (need either sqlite_db_path or postgres_config)")
        
        if db_type == "sqlite":
            logger.debug("VannaManager: Connecting to SQLite database...")
            vn_instance.connect_to_sqlite(self.sqlite_db_path)
        elif db_type == "postgresql":
            # Check if we have pre-configured postgres parameters (preferred)
            if hasattr(self, 'postgres_config') and self.postgres_config:
                logger.info(f"VannaManager: Using pre-configured PostgreSQL parameters")
                pg_params = self.postgres_config
                logger.info(f"VannaManager: Params - host={pg_params['host']}, port={pg_params['port']}, dbname={pg_params['dbname']}, user={pg_params['user']}")
            else:
                # This shouldn't happen if configured properly
                logger.error("VannaManager: PostgreSQL type detected but no postgres_config available!")
                raise ValueError("PostgreSQL configuration missing - use individual postgres_* fields in config")
            
            logger.debug("VannaManager: Connecting to PostgreSQL database...")
            vn_instance.connect_to_postgres(**pg_params)
        else:
            raise ValueError(
                f"VannaManager: Unsupported database type: {db_type}. "
                f"Supported types: 'sqlite', 'postgresql'"
            )

        # Set configuration - allow LLM to see data for database introspection
        vn_instance.allow_llm_to_see_data = True
        logger.debug("VannaManager: Set allow_llm_to_see_data = True")

        # Initialize if needed (check if vector store is empty)
        needs_init = self._needs_initialization()
        if needs_init:
            logger.info(
                "VannaManager: Vector store needs initialization, starting training..."
            )
            try:
                initVanna(vn_instance, self.training_data_path, db_type)
                logger.info("VannaManager: Vector store initialization complete")
            except Exception as e:
                logger.error(f"VannaManager: Error during initialization: {e}")
                raise
        else:
            logger.debug(
                "VannaManager: Vector store already initialized, skipping training"
            )
        return vn_instance

    def _mask_db_connection(self, connection_string: str) -> str:
        """
        Mask sensitive information in database connection string for logging.
        
        Args:
            connection_string: Database connection string
            
        Returns:
            Masked connection string
        """
        if not connection_string:
            return "None"
        
        # For PostgreSQL connection strings, mask password
        if connection_string.startswith(("postgresql://", "postgres://")):
            from urllib.parse import urlparse
            try:
                parsed = urlparse(connection_string)
                if parsed.password:
                    return connection_string.replace(parsed.password, "****")
            except:
                pass
        
        # For file paths, just return as is
        return connection_string

    def _needs_initialization(self) -> bool:
        """
        Check if the vector store needs initialization by checking if it's empty.
        For ChromaDB: checks if directory exists and has data.
        For Milvus: checks if collection exists and has data.
        """
        logger.debug("VannaManager: Checking if vector store needs initialization...")
        
        if self.use_milvus:
            # For Milvus, check if collection exists and has data
            logger.debug("VannaManager: Checking Milvus collection status...")
            try:
                from pymilvus import MilvusClient
                
                client = MilvusClient(
                    uri=self.milvus_config.get("uri"),
                    user=self.milvus_config.get("user"),
                    password=self.milvus_config.get("password"),
                )
                
                collection_name = self.milvus_config.get("collection_name", "vanna_embeddings")
                collections = client.list_collections()
                
                if collection_name not in collections:
                    logger.debug(f"VannaManager: Milvus collection {collection_name} does not exist -> needs initialization")
                    return True
                
                # Check if collection has data
                stats = client.get_collection_stats(collection_name=collection_name)
                row_count = stats.get("row_count", 0)
                
                logger.debug(f"VannaManager: Milvus collection has {row_count} rows")
                
                if row_count > 0:
                    logger.debug("VannaManager: Milvus collection is populated -> skipping initialization")
                    return False
                else:
                    logger.debug("VannaManager: Milvus collection is empty -> needs initialization")
                    return True
                    
            except Exception as e:
                logger.warning(f"VannaManager: Could not check Milvus status: {e}")
                logger.warning("VannaManager: Defaulting to needs initialization = True")
                return True
        else:
            # For ChromaDB, check directory
            logger.debug(f"VannaManager: Vector store path: {self.vector_store_path}")

            try:
                if not os.path.exists(self.vector_store_path):
                    logger.debug(
                        "VannaManager: Vector store directory does not exist -> needs initialization"
                    )
                    return True

                # Check if there are any subdirectories (ChromaDB creates subdirectories when data is stored)
                list_of_folders = [
                    d
                    for d in os.listdir(self.vector_store_path)
                    if os.path.isdir(os.path.join(self.vector_store_path, d))
                ]

                logger.debug(
                    f"VannaManager: Found {len(list_of_folders)} folders in vector store"
                )
                if list_of_folders:
                    logger.debug(f"VannaManager: Vector store folders: {list_of_folders}")
                    logger.debug(
                        "VannaManager: Vector store is populated -> skipping initialization"
                    )
                    return False
                else:
                    logger.debug(
                        "VannaManager: Vector store is empty -> needs initialization"
                    )
                    return True

            except Exception as e:
                logger.warning(f"VannaManager: Could not check vector store status: {e}")
                logger.warning("VannaManager: Defaulting to needs initialization = True")
                return True

    def generate_sql_safe(self, question: str) -> str:
        """
        Generate SQL with error handling.
        """
        with self.lock:
            if self.vanna_instance is None:
                raise RuntimeError("VannaManager: No instance available")

            try:
                logger.debug(f"VannaManager: Generating SQL for question: {question}")

                # Generate SQL with allow_llm_to_see_data=True for database introspection
                sql = self.vanna_instance.generate_sql(
                    question=question, allow_llm_to_see_data=True
                )

                # Validate SQL response
                if not sql or sql.strip() == "":
                    raise ValueError("Empty SQL response")

                return sql

            except Exception as e:
                logger.error(f"VannaManager: Error in SQL generation: {e}")
                raise

    def force_reset(self):
        """
        Force reset the instance (useful for cleanup).
        """
        with self.lock:
            if self.vanna_instance:
                logger.debug(f"VannaManager: Resetting instance for {self.config_key}")
                self.vanna_instance = None

    def get_stats(self) -> Dict:
        """
        Get manager statistics.
        """
        return {
            "config_key": self.config_key,
            "instance_id": id(self.vanna_instance) if self.vanna_instance else None,
            "has_instance": self.vanna_instance is not None,
        }

    @classmethod
    def create_with_config(
        cls,
        vanna_llm_config,
        vanna_embedder_config,
        vector_store_path: str = None,
        sqlite_db_path: str = None,
        training_data_path: str = None,
        # PostgreSQL individual fields (recommended for production)
        postgres_host: str = None,
        postgres_port: int = 5432,
        postgres_user: str = None,
        postgres_password: str = None,
        postgres_dbname: str = None,
        postgres_schema: str = "public",
        # Milvus configuration (for IT-managed production deployments)
        use_milvus: bool = False,
        milvus_uri: str = None,
        milvus_user: str = None,
        milvus_password: str = None,
        milvus_collection_name: str = "vanna_embeddings",
    ):
        """
        Class method to create a VannaManager with full configuration.
        Uses create_config_key to ensure singleton behavior based on configuration.
        
        Database options:
        - For SQLite (local development): Use sqlite_db_path parameter.
        - For PostgreSQL (production): Use individual postgres_* parameters.
        
        Vector store options:
        - For ChromaDB (local): Use vector_store_path, set use_milvus=False
        - For Milvus (IT-managed production): Use milvus_* parameters, set use_milvus=True
        """
        # Determine database configuration approach
        db_config_str = None
        postgres_config = None
        
        # Check if individual PostgreSQL fields are provided (recommended for production)
        if postgres_host and postgres_user and postgres_password and postgres_dbname:
            logger.info(f"VannaManager.create_with_config: Using individual PostgreSQL fields")
            logger.info(f"  Host: {postgres_host}, Port: {postgres_port}, DB: {postgres_dbname}, Schema: {postgres_schema}")
            postgres_config = {
                'host': postgres_host,
                'port': postgres_port,
                'user': postgres_user,
                'password': postgres_password,
                'dbname': postgres_dbname,
                'options': f'-csearch_path={postgres_schema}' if postgres_schema else None,
            }
            # Create a connection string for config key generation
            db_config_str = f"postgresql://{postgres_user}:****@{postgres_host}:{postgres_port}/{postgres_dbname}"
        elif sqlite_db_path:
            logger.info(f"VannaManager.create_with_config: Using SQLite database at: {sqlite_db_path}")
            db_config_str = sqlite_db_path
        else:
            raise ValueError("Must provide either sqlite_db_path (for SQLite) or individual postgres_* fields (for PostgreSQL)")
        
        # Configure vector store
        milvus_config = None
        vector_config_str = None
        
        if use_milvus:
            if not all([milvus_uri, milvus_user, milvus_password]):
                raise ValueError("When use_milvus=True, must provide milvus_uri, milvus_user, and milvus_password")
            
            logger.info(f"VannaManager.create_with_config: Using Milvus vector store")
            logger.info(f"  URI: {milvus_uri}, Collection: {milvus_collection_name}")
            
            milvus_config = {
                'uri': milvus_uri,
                'user': milvus_user,
                'password': milvus_password,
                'collection_name': milvus_collection_name,
            }
            vector_config_str = f"milvus://{milvus_uri}/{milvus_collection_name}"
        else:
            if not vector_store_path:
                raise ValueError("When use_milvus=False, must provide vector_store_path for ChromaDB")
            
            logger.info(f"VannaManager.create_with_config: Using ChromaDB vector store at: {vector_store_path}")
            vector_config_str = vector_store_path
        
        config_key = create_config_key(
            vanna_llm_config, vanna_embedder_config, vector_config_str, db_config_str
        )

        # Create instance with just config_key (singleton pattern)
        instance = cls(config_key)

        # If this is a new instance that hasn't been configured yet, set the configuration
        if (
            not hasattr(instance, "vanna_llm_config")
            or instance.vanna_llm_config is None
        ):
            instance.vanna_llm_config = vanna_llm_config
            instance.vanna_embedder_config = vanna_embedder_config
            instance.vector_store_path = vector_store_path
            instance.sqlite_db_path = sqlite_db_path
            instance.training_data_path = training_data_path
            instance.postgres_config = postgres_config  # Store parsed postgres config if available
            instance.milvus_config = milvus_config
            instance.use_milvus = use_milvus
            
            if postgres_config:
                logger.info(f"VannaManager.create_with_config: Stored PostgreSQL config directly (no parsing needed)")
            else:
                logger.info(f"VannaManager.create_with_config: Using SQLite database at: {instance.sqlite_db_path}")
            
            if use_milvus:
                logger.info(f"VannaManager.create_with_config: Using Milvus vector store")
            else:
                logger.info(f"VannaManager.create_with_config: Using ChromaDB vector store at: {instance.vector_store_path}")

            # Create Vanna instance immediately if all config is available
            if instance.vanna_instance is None:
                logger.debug(
                    "VannaManager: Creating Vanna instance for existing singleton"
                )
                instance.vanna_instance = instance._create_instance()

        return instance


def create_config_key(
    vanna_llm_config, vanna_embedder_config, vector_store_path: str, db_config_str: str
) -> str:
    """
    Create a unique configuration key for the VannaManager singleton.
    
    Args:
        vanna_llm_config: LLM configuration
        vanna_embedder_config: Embedder configuration  
        vector_store_path: Path to vector store
        db_config_str: Database configuration string (SQLite path or PostgreSQL identifier)
    """
    config_str = f"{vanna_llm_config.model_name}_{vanna_embedder_config.model_name}_{vector_store_path}_{db_config_str}"
    return hashlib.md5(config_str.encode()).hexdigest()[:12]
