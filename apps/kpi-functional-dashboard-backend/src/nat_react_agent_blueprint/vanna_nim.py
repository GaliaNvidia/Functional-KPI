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
from langchain_nvidia import ChatNVIDIA
import logging

logger = logging.getLogger(__name__)


class NIMCustomLLM(VannaBase):
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
            raise ValueError("config must contain a NIM api_key")

        if "model" not in config:
            raise ValueError("config must contain a NIM model")

        api_key = config["api_key"]
        model = config["model"]

        # Initialize ChatNVIDIA client
        self.client = ChatNVIDIA(
            api_key=api_key,
            model=model,
            temperature=self.temperature,
        )
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
            response = self.client.invoke(prompt)
            logger.debug(f"Response type: {type(response)}")
            logger.debug(f"Response content type: {type(response.content)}")
            logger.debug(f"Response content length: {len(response.content) if response.content else 0}")
            logger.debug(f"Response content preview: {response.content[:200] if response.content else 'None'}...")
            return response.content
        except Exception as e:
            logger.error(f"Error in submit_prompt: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise


class NIMVanna(ChromaDB_VectorStore, NIMCustomLLM):
    def __init__(self, VectorConfig=None, LLMConfig=None):
        ChromaDB_VectorStore.__init__(self, config=VectorConfig)
        NIMCustomLLM.__init__(self, config=LLMConfig)


class NVIDIAEmbeddingFunction:
    """
    A class that can be used as a replacement for chroma's DefaultEmbeddingFunction.
    It takes in input (text or list of texts) and returns embeddings using NVIDIA's API.
    
    This class fixes two major interface compatibility issues between ChromaDB and NVIDIA embeddings:
    
    1. INPUT FORMAT MISMATCH:
       - ChromaDB passes ['query text'] (list) to embed_query()
       - But langchain_nvidia's embed_query() expects 'query text' (string)
       - When list is passed, langchain does [text] internally → [['query text']] → API 500 error
       - FIX: Detect list input and extract string before calling langchain
    
    2. OUTPUT FORMAT MISMATCH:
       - ChromaDB expects embed_query() to return [[embedding_vector]] (list of embeddings)
       - But langchain returns [embedding_vector] (single embedding vector)
       - This causes: TypeError: 'float' object cannot be converted to 'Sequence'
       - FIX: Wrap single embedding in list: return [embeddings]
    """

    def __init__(self, api_key, model="nvidia/llama-3.2-nv-embedqa-1b-v2"):
        """
        Initialize the embedding function with the API key and model name.

        Parameters:
        - api_key (str): The API key for authentication.
        - model (str): The model name to use for embeddings.
                      Default: nvidia/llama-3.2-nv-embedqa-1b-v2 (tested and working)
        """
        from langchain_nvidia import NVIDIAEmbeddings
        
        self.api_key = api_key
        self.model = model
        
        logger.info(f"Initializing NVIDIA embeddings with model: {model}")
        logger.debug(f"API key length: {len(api_key) if api_key else 0}")
        
        self.embeddings = NVIDIAEmbeddings(
            api_key=api_key,
            model_name=model,
            input_type="query",
            truncate="NONE"
        )
        logger.info(f"Successfully initialized NVIDIA embeddings")

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
        
        # Generate embeddings for each text
        embeddings = []
        for i, text in enumerate(input_data):
            logger.debug(f"Embedding text {i+1}/{len(input_data)}: {text[:50]}...")
            embedding = self.embeddings.embed_query(text)
            embeddings.append(embedding)
        
        logger.debug(f"Generated {len(embeddings)} embeddings")
        # Always return a list of embeddings for ChromaDB
        return embeddings
    
    def name(self):
        """
        Returns a custom name for the embedding function.

        Returns:
            str: The name of the embedding function.
        """
        return "NVIDIA Embedding Function"
    
    def embed_query(self, input: str) -> list[list[float]]:
        """
        Generate embeddings for a single query.
        
        ChromaDB calls this method with ['query text'] (list) but langchain_nvidia expects 'query text' (string).
        We must extract the string from the list to prevent API 500 errors.
        
        ChromaDB expects this method to return [[embedding_vector]] (list of embeddings) 
        but langchain returns [embedding_vector] (single embedding). We wrap it in a list.
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
            # Call langchain_nvidia with the extracted string
            embeddings = self.embeddings.embed_query(query_text)
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
        # This function expects a list of strings. If it's a list of lists of strings, flatten it to handle cases
        # where the input is unexpectedly nested.
        logger.debug(f"Embedding {len(input)} documents...")
        logger.debug(f"Using model: {self.model}")
        
        try:
            embeddings = self.embeddings.embed_documents(input)
            logger.debug(f"Successfully generated document embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"Error generating document embeddings: {e}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Input documents count: {len(input)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

