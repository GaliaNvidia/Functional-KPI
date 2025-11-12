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
Milvus vector store implementation for Vanna AI.
Provides integration with IT-managed Milvus databases for production deployments.
"""

import logging
import uuid
from typing import List
import pandas as pd
from vanna.base import VannaBase

# Import existing LLM implementations
from nat_react_agent_blueprint.vanna_nim import NIMCustomLLM
from nat_react_agent_blueprint.vanna_openai import OpenAICustomLLM

logger = logging.getLogger(__name__)


class MilvusDB_VectorStore:
    """
    Milvus vector store implementation for Vanna.
    Compatible with Vanna's vector store interface and supports IT-managed Milvus instances.
    """

    def __init__(self, config=None):
        """
        Initialize Milvus vector store.
        
        Args:
            config: Dictionary containing Milvus configuration:
                - uri: Milvus server URI (e.g., "https://milvus-astra-users-dev.db.nvw.nvidia.com")
                - user: Username for authentication
                - password: Password for authentication
                - collection_name: Name of the collection to use (default: "vanna_embeddings")
                - embedding_function: Embedding function to use (required)
        """
        if config is None:
            config = {}
            
        self.config = config
        self.collection_name = config.get("collection_name", "vanna_embeddings")
        self.embedding_function = config.get("embedding_function")
        
        if not self.embedding_function:
            raise ValueError("embedding_function is required in config")
        
        # Import Milvus client
        try:
            from pymilvus import MilvusClient, DataType
            self.MilvusClient = MilvusClient
            self.DataType = DataType
        except ImportError:
            raise ImportError(
                "pymilvus is not installed. Install it with: pip install pymilvus"
            )
        
        # Initialize Milvus client
        uri = config.get("uri")
        user = config.get("user")
        password = config.get("password")
        
        if not all([uri, user, password]):
            raise ValueError(
                "Milvus configuration requires 'uri', 'user', and 'password'"
            )
        
        logger.info(f"Connecting to Milvus at {uri} with user {user}")
        
        self.milvus_client = self.MilvusClient(
            uri=uri,
            user=user,
            password=password,
        )
        
        # Check if collection already exists
        self._collection_initialized = False
        self._embedding_dim = None
        
        try:
            collections = self.milvus_client.list_collections()
            if self.collection_name in collections:
                self._collection_initialized = True
                logger.info(f"Milvus collection '{self.collection_name}' already exists")
                # Get stats to show collection info
                stats = self.milvus_client.get_collection_stats(collection_name=self.collection_name)
                row_count = stats.get("row_count", 0)
                logger.info(f"Collection has {row_count} existing rows")
            else:
                logger.info(f"Milvus collection '{self.collection_name}' will be created on first use")
        except Exception as e:
            logger.warning(f"Could not check collection status: {e}")
        
        logger.info(f"Milvus client initialized for collection: {self.collection_name}")
    
    def _ensure_collection_exists(self, embedding_dim: int):
        """
        Ensure the collection exists with the correct schema.
        Creates the collection if it doesn't exist.
        
        Args:
            embedding_dim: Dimension of the embedding vectors
        """
        if self._collection_initialized:
            return
            
        # Check if collection exists
        collections = self.milvus_client.list_collections()
        
        if self.collection_name not in collections:
            logger.info(f"Creating Milvus collection: {self.collection_name}")
            
            # Create collection with schema
            schema = self.milvus_client.create_schema(
                auto_id=False,
                enable_dynamic_field=True,
            )
            
            # Add fields
            schema.add_field(field_name="id", datatype=self.DataType.VARCHAR, is_primary=True, max_length=100)
            schema.add_field(field_name="embedding", datatype=self.DataType.FLOAT_VECTOR, dim=embedding_dim)
            schema.add_field(field_name="doc", datatype=self.DataType.VARCHAR, max_length=65535)
            
            # Create index for vector field
            index_params = self.milvus_client.prepare_index_params()
            index_params.add_index(
                field_name="embedding",
                index_type="AUTOINDEX",
                metric_type="COSINE",
            )
            
            # Create collection
            self.milvus_client.create_collection(
                collection_name=self.collection_name,
                schema=schema,
                index_params=index_params,
            )
            
            logger.info(f"Collection {self.collection_name} created successfully")
        else:
            logger.debug(f"Collection {self.collection_name} already exists")
        
        self._collection_initialized = True
        self._embedding_dim = embedding_dim
    
    def add_question_sql(self, question: str, sql: str, **kwargs) -> str:
        """
        Add a question-SQL pair to the vector store.
        
        Args:
            question: The question text
            sql: The SQL query
            **kwargs: Additional metadata
            
        Returns:
            ID of the added document
        """
        doc = f"Question: {question}\nSQL: {sql}"
        return self.add_documentation(doc, **kwargs)
    
    def add_ddl(self, ddl: str, **kwargs) -> str:
        """
        Add DDL statement to the vector store.
        
        Args:
            ddl: The DDL statement
            **kwargs: Additional metadata
            
        Returns:
            ID of the added document
        """
        doc = f"DDL: {ddl}"
        return self.add_documentation(doc, **kwargs)
    
    def add_documentation(self, documentation: str, **kwargs) -> str:
        """
        Add documentation to the vector store.
        
        Args:
            documentation: The documentation text
            **kwargs: Additional metadata
            
        Returns:
            ID of the added document
        """
        # Generate embedding
        embedding = self.embedding_function([documentation])[0]
        embedding_dim = len(embedding)
        
        # Ensure collection exists with correct dimension
        self._ensure_collection_exists(embedding_dim)
        
        # Generate unique ID
        doc_id = str(uuid.uuid4())
        
        # Prepare data
        data = [{
            "id": doc_id,
            "embedding": embedding,
            "doc": documentation,
        }]
        
        # Insert into Milvus
        try:
            self.milvus_client.insert(
                collection_name=self.collection_name,
                data=data,
            )
            logger.debug(f"Added document with ID: {doc_id}")
            return doc_id
        except Exception as e:
            logger.error(f"Error adding document to Milvus: {e}")
            raise
    
    def get_similar_question_sql(self, question: str, **kwargs) -> list:
        """
        Get similar question-SQL pairs from the vector store.
        
        Args:
            question: The question to search for
            **kwargs: Additional search parameters
            
        Returns:
            List of similar question-SQL pairs with scores
        """
        if not self._collection_initialized:
            logger.warning("Collection not initialized, no data available")
            return []
        
        # Generate embedding for the question
        embedding = self.embedding_function([question])[0]
        
        # Search in Milvus
        try:
            results = self.milvus_client.search(
                collection_name=self.collection_name,
                data=[embedding],
                limit=kwargs.get("limit", 10),
                output_fields=["doc"],
            )
            
            # Format results
            similar_docs = []
            if results and len(results) > 0:
                for hit in results[0]:
                    doc = hit.get("entity", {}).get("doc", "")
                    score = hit.get("distance", 0.0)
                    
                    # Parse question and SQL from doc
                    if "Question:" in doc and "SQL:" in doc:
                        similar_docs.append({
                            "question": doc.split("Question:")[1].split("SQL:")[0].strip(),
                            "sql": doc.split("SQL:")[1].strip(),
                            "score": score,
                        })
            
            logger.debug(f"Found {len(similar_docs)} similar question-SQL pairs")
            return similar_docs
            
        except Exception as e:
            logger.error(f"Error searching Milvus: {e}")
            return []
    
    def get_related_ddl(self, question: str, **kwargs) -> list:
        """
        Get related DDL statements from the vector store.
        
        Args:
            question: The question to search for
            **kwargs: Additional search parameters
            
        Returns:
            List of related DDL statements
        """
        if not self._collection_initialized:
            logger.warning("Collection not initialized, no data available")
            return []
        
        # Generate embedding for the question
        embedding = self.embedding_function([question])[0]
        
        # Search in Milvus
        try:
            results = self.milvus_client.search(
                collection_name=self.collection_name,
                data=[embedding],
                limit=kwargs.get("limit", 10),
                output_fields=["doc"],
            )
            
            # Format results
            ddl_list = []
            if results and len(results) > 0:
                for hit in results[0]:
                    doc = hit.get("entity", {}).get("doc", "")
                    
                    # Extract DDL from doc
                    if "DDL:" in doc:
                        ddl = doc.split("DDL:")[1].strip()
                        ddl_list.append(ddl)
            
            logger.debug(f"Found {len(ddl_list)} related DDL statements")
            return ddl_list
            
        except Exception as e:
            logger.error(f"Error searching Milvus: {e}")
            return []
    
    def get_related_documentation(self, question: str, **kwargs) -> list:
        """
        Get related documentation from the vector store.
        
        Args:
            question: The question to search for
            **kwargs: Additional search parameters
            
        Returns:
            List of related documentation
        """
        if not self._collection_initialized:
            logger.warning("Collection not initialized, no data available")
            return []
        
        # Generate embedding for the question
        embedding = self.embedding_function([question])[0]
        
        # Search in Milvus
        try:
            results = self.milvus_client.search(
                collection_name=self.collection_name,
                data=[embedding],
                limit=kwargs.get("limit", 10),
                output_fields=["doc"],
            )
            
            # Format results
            docs = []
            if results and len(results) > 0:
                for hit in results[0]:
                    doc = hit.get("entity", {}).get("doc", "")
                    docs.append(doc)
            
            logger.debug(f"Found {len(docs)} related documentation entries")
            return docs
            
        except Exception as e:
            logger.error(f"Error searching Milvus: {e}")
            return []
    
    def get_training_data(self, **kwargs) -> pd.DataFrame:
        """
        Get all training data from the vector store.
        
        Returns:
            DataFrame containing all training data
        """
        if not self._collection_initialized:
            logger.warning("Collection not initialized, no data available")
            return pd.DataFrame()
        
        try:
            # Query all data
            results = self.milvus_client.query(
                collection_name=self.collection_name,
                filter="",
                output_fields=["id", "doc"],
                limit=10000,  # Adjust limit as needed
            )
            
            # Convert to DataFrame
            if results:
                return pd.DataFrame(results)
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error getting training data from Milvus: {e}")
            return pd.DataFrame()
    
    def remove_training_data(self, id: str, **kwargs) -> bool:
        """
        Remove training data by ID.
        
        Args:
            id: The ID of the document to remove
            
        Returns:
            True if successful, False otherwise
        """
        if not self._collection_initialized:
            logger.warning("Collection not initialized")
            return False
        
        try:
            self.milvus_client.delete(
                collection_name=self.collection_name,
                ids=[id],
            )
            logger.info(f"Removed document with ID: {id}")
            return True
        except Exception as e:
            logger.error(f"Error removing document from Milvus: {e}")
            return False

class NIMVannaMilvus(MilvusDB_VectorStore, NIMCustomLLM):
    """Vanna with NIM LLM and Milvus vector store"""
    
    def __init__(self, VectorConfig=None, LLMConfig=None):
        MilvusDB_VectorStore.__init__(self, config=VectorConfig)
        NIMCustomLLM.__init__(self, config=LLMConfig)
    
    def generate_embedding(self, data: str, **kwargs) -> List[float]:
        """
        Generate embedding for a single text string.
        Required by Vanna's base class.
        """
        embedding_result = self.embedding_function([data])
        if isinstance(embedding_result, list) and len(embedding_result) > 0:
            return embedding_result[0]
        return embedding_result


class OpenAIVannaMilvus(MilvusDB_VectorStore, OpenAICustomLLM):
    """Vanna with OpenAI LLM and Milvus vector store"""
    
    def __init__(self, VectorConfig=None, LLMConfig=None):
        MilvusDB_VectorStore.__init__(self, config=VectorConfig)
        OpenAICustomLLM.__init__(self, config=LLMConfig)
    
    def generate_embedding(self, data: str, **kwargs) -> List[float]:
        """
        Generate embedding for a single text string.
        Required by Vanna's base class.
        """
        embedding_result = self.embedding_function([data])
        if isinstance(embedding_result, list) and len(embedding_result) > 0:
            return embedding_result[0]
        return embedding_result


class MilvusNVIDIAEmbeddingFunction:
    """
    NVIDIA embedding function compatible with Milvus.
    Returns embeddings as list of floats (not nested lists).
    """

    def __init__(self, api_key, model="nvidia/llama-3.2-nv-embedqa-1b-v2"):
        """
        Initialize the embedding function with the API key and model name.

        Parameters:
        - api_key (str): The API key for authentication.
        - model (str): The model name to use for embeddings.
                      Default: nvidia/llama-3.2-nv-embedqa-1b-v2
        """
        from langchain_nvidia import NVIDIAEmbeddings
        
        self.api_key = api_key
        self.model = model
        
        logger.info(f"Initializing NVIDIA embeddings for Milvus with model: {model}")
        
        self.embeddings = NVIDIAEmbeddings(
            api_key=api_key,
            model_name=model,
            input_type="query",
            truncate="NONE"
        )
        logger.info(f"Successfully initialized NVIDIA embeddings for Milvus")

    def __call__(self, input):
        """
        Generate embeddings for input text(s).
        Returns list of embedding vectors (not nested).
        
        Parameters:
        - input (str or list): The input data for which embeddings need to be generated.
        
        Returns:
        - list: Embedding vector(s) for the input data
        """
        logger.debug(f"Generating embeddings for input type: {type(input)}")
        
        # Ensure input is a list
        if isinstance(input, str):
            input_data = [input]
        else:
            input_data = input
        
        logger.debug(f"Processing {len(input_data)} texts for embedding")
        
        # Generate embeddings for each text
        embeddings = []
        for i, text in enumerate(input_data):
            logger.debug(f"Embedding text {i+1}/{len(input_data)}: {text[:50]}...")
            embedding = self.embeddings.embed_query(text)
            embeddings.append(embedding)
        
        logger.debug(f"Generated {len(embeddings)} embeddings")
        return embeddings


class MilvusOpenAIEmbeddingFunction:
    """
    OpenAI embedding function compatible with Milvus.
    Returns embeddings as list of floats (not nested lists).
    """

    def __init__(self, api_key, model="text-embedding-3-small", base_url=None):
        """
        Initialize the embedding function with the API key and model name.

        Parameters:
        - api_key (str): The API key for authentication.
        - model (str): The model name to use for embeddings.
        - base_url (str, optional): Custom base URL for OpenAI-compatible endpoints
        """
        from openai import OpenAI
        
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        
        logger.info(f"Initializing OpenAI embeddings for Milvus with model: {model}")
        if base_url:
            logger.info(f"Using custom base_url: {base_url}")
        
        # Initialize OpenAI client
        if base_url:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = OpenAI(api_key=api_key)
        logger.info(f"Successfully initialized OpenAI embeddings for Milvus")

    def __call__(self, input):
        """
        Generate embeddings for input text(s).
        Returns list of embedding vectors (not nested).
        
        Parameters:
        - input (str or list): The input data for which embeddings need to be generated.
        
        Returns:
        - list: Embedding vector(s) for the input data
        """
        logger.debug(f"Generating embeddings for input type: {type(input)}")
        
        # Ensure input is a list
        if isinstance(input, str):
            input_data = [input]
        else:
            input_data = input
        
        logger.debug(f"Processing {len(input_data)} texts for embedding")
        
        try:
            # OpenAI can handle batch requests
            response = self.client.embeddings.create(
                model=self.model,
                input=input_data,
                extra_body={"input_type": "passage"}
            )
            
            # Extract embeddings from response
            embeddings = [data.embedding for data in response.data]
            
            logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

