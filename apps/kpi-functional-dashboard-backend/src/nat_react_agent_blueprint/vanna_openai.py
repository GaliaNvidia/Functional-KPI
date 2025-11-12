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

from vanna.chromadb import ChromaDB_VectorStore
from vanna.base import VannaBase
import logging

logger = logging.getLogger(__name__)


class OpenAICustomLLM(VannaBase):
    def __init__(self, config=None):
        VannaBase.__init__(self, config=config)

        if not config:
            raise ValueError("config must be passed")

        # default parameters - can be overrided using config
        self.temperature = 0.7

        if "temperature" in config:
            self.temperature = config["temperature"]

        # If only config is passed
        if "api_key" not in config:
            raise ValueError("config must contain an api_key")

        if "model" not in config:
            raise ValueError("config must contain a model")

        api_key = config["api_key"]
        model = config["model"]
        
        # Support for custom OpenAI-compatible endpoints (e.g., DataRobot, Azure, etc.)
        base_url = config.get("base_url", None)

        # Initialize OpenAI client with optional base_url for custom endpoints
        from openai import OpenAI
        if base_url:
            logger.info(f"Initializing OpenAI-compatible client with custom base_url: {base_url}")
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            logger.info("Initializing OpenAI client with default endpoint")
            self.client = OpenAI(api_key=api_key)
        self.model = model

    def system_message(self, message: str) -> any:
        return {
            "role": "system",
            "content": message
            + "\n DO NOT PRODUCE MARKDOWN, ONLY RESPOND IN PLAIN TEXT",
        }

    def user_message(self, message: str) -> any:
        return {"role": "user", "content": message}

    def assistant_message(self, message: str) -> any:
        return {"role": "assistant", "content": message}

    def submit_prompt(self, prompt, **kwargs) -> str:
        if prompt is None:
            raise Exception("Prompt is None")

        if len(prompt) == 0:
            raise Exception("Prompt is empty")

        # Count the number of tokens in the message log
        # Use 4 as an approximation for the number of characters per token
        num_tokens = 0
        for message in prompt:
            num_tokens += len(message["content"]) / 4
        print(f"Using model {self.model} for {num_tokens} tokens (approx)")
        
        logger.debug(f"Submitting prompt with {len(prompt)} messages")
        logger.debug(f"Prompt content preview: {str(prompt)[:500]}...")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=prompt,
                temperature=self.temperature
            )
            content = response.choices[0].message.content
            logger.debug(f"Response type: {type(response)}")
            logger.debug(f"Response content type: {type(content)}")
            logger.debug(f"Response content length: {len(content) if content else 0}")
            logger.debug(f"Response content preview: {content[:200] if content else 'None'}...")
            return content
        except Exception as e:
            logger.error(f"Error in submit_prompt: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise


class OpenAIVanna(ChromaDB_VectorStore, OpenAICustomLLM):
    def __init__(self, VectorConfig=None, LLMConfig=None):
        ChromaDB_VectorStore.__init__(self, config=VectorConfig)
        OpenAICustomLLM.__init__(self, config=LLMConfig)


class OpenAIEmbeddingFunction:
    """
    A class that can be used as a replacement for chroma's DefaultEmbeddingFunction.
    It takes in input (text or list of texts) and returns embeddings using OpenAI's API.
    
    This class fixes two major interface compatibility issues between ChromaDB and OpenAI embeddings:
    
    1. INPUT FORMAT MISMATCH:
       - ChromaDB passes ['query text'] (list) to embed_query()
       - But OpenAI's create() expects 'query text' (string)
       - When list is passed, we need to extract the string
       - FIX: Detect list input and extract string before calling OpenAI API
    
    2. OUTPUT FORMAT MISMATCH:
       - ChromaDB expects embed_query() to return [[embedding_vector]] (list of embeddings)
       - But OpenAI returns embedding_vector (single embedding vector)
       - This causes: TypeError: 'float' object cannot be converted to 'Sequence'
       - FIX: Wrap single embedding in list: return [embeddings]
    """

    def __init__(self, api_key, model="text-embedding-3-small", base_url=None):
        """
        Initialize the embedding function with the API key and model name.

        Parameters:
        - api_key (str): The API key for authentication.
        - model (str): The model name to use for embeddings.
                      Default: text-embedding-3-small (efficient and cost-effective)
                      Alternatives: text-embedding-3-large, text-embedding-ada-002
        - base_url (str, optional): Custom base URL for OpenAI-compatible endpoints
                                   (e.g., DataRobot, Azure OpenAI, etc.)
        """
        from openai import OpenAI
        
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        
        logger.info(f"Initializing OpenAI embeddings with model: {model}")
        logger.debug(f"API key length: {len(api_key) if api_key else 0}")
        if base_url:
            logger.info(f"Using custom base_url: {base_url}")
        
        # Initialize OpenAI client with optional base_url for custom endpoints
        if base_url:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = OpenAI(api_key=api_key)
        logger.info(f"Successfully initialized OpenAI embeddings")

    def __call__(self, input):
        """
        Call method to make the object callable, as required by chroma's EmbeddingFunction interface.
        
        NOTE: This method is used by ChromaDB for batch embedding operations.
        The embed_query() method above handles the single query case with the critical fixes.

        Parameters:
        - input (str or list): The input data for which embeddings need to be generated.

        Returns:
        - embedding (list): The embedding vector(s) for the input data.
        """
        logger.debug(f"__call__ method called with input type: {type(input)}")
        logger.debug(f"__call__ input: {input}")
        
        # Ensure input is a list, as required by ChromaDB
        if isinstance(input, str):
            input_data = [input]
        else:
            input_data = input
        
        logger.debug(f"Processing {len(input_data)} texts for embedding")
        
        try:
            # OpenAI can handle batch requests, so we pass the list directly
            # Add input_type for DataRobot/NIM endpoints that require it
            response = self.client.embeddings.create(
                model=self.model,
                input=input_data,
                extra_body={"input_type": "passage"}  # Use "passage" for document embedding
            )
            
            # Extract embeddings from response
            embeddings = [data.embedding for data in response.data]
            
            logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
    def name(self):
        """
        Returns a custom name for the embedding function.

        Returns:
            str: The name of the embedding function.
        """
        return "OpenAI Embedding Function"
    
    def embed_query(self, input: str) -> list[list[float]]:
        """
        Generate embeddings for a single query.
        
        ChromaDB calls this method with ['query text'] (list) but OpenAI expects 'query text' (string).
        We must extract the string from the list to prevent API errors.
        
        ChromaDB expects this method to return [[embedding_vector]] (list of embeddings) 
        but OpenAI returns embedding_vector (single embedding). We wrap it in a list.
        """
        logger.debug(f"Embedding query: {input}")
        logger.debug(f"Input type: {type(input)}")
        logger.debug(f"Using model: {self.model}")
        
        # Handle ChromaDB's list input format
        # ChromaDB sometimes passes a list instead of a string
        # Extract the string from the list if needed
        if isinstance(input, list):
            if len(input) == 1:
                query_text = input[0]
                logger.debug(f"Extracted string from list: {query_text}")
            else:
                logger.error(f"Unexpected list length: {len(input)}")
                raise ValueError(f"Expected single string or list with one element, got list with {len(input)} elements")
        else:
            query_text = input
        
        try:
            # Call OpenAI API with the extracted string
            # Add input_type for DataRobot/NIM endpoints that require it
            response = self.client.embeddings.create(
                model=self.model,
                input=query_text,
                extra_body={"input_type": "query"}  # Use "query" for search queries
            )
            
            embeddings = response.data[0].embedding
            logger.debug(f"Successfully generated embeddings of length: {len(embeddings) if embeddings else 0}")
            
            # Wrap single embedding in list for ChromaDB compatibility
            # ChromaDB expects a list of embeddings, even for a single query
            return [embeddings]
        except Exception as e:
            logger.error(f"Error generating embeddings for query: {e}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Query text: {query_text}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
    def embed_documents(self, input: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple documents.
        
        Parameters:
        - input (list[str]): List of documents to embed.
        
        Returns:
        - list[list[float]]: List of embedding vectors.
        """
        logger.debug(f"Embedding {len(input)} documents...")
        logger.debug(f"Using model: {self.model}")
        
        try:
            # Add input_type for DataRobot/NIM endpoints that require it
            response = self.client.embeddings.create(
                model=self.model,
                input=input,
                extra_body={"input_type": "passage"}  # Use "passage" for documents
            )
            
            embeddings = [data.embedding for data in response.data]
            logger.debug(f"Successfully generated document embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"Error generating document embeddings: {e}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Input documents count: {len(input)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

