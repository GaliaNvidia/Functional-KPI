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

import logging

logger = logging.getLogger(__name__)


def chunk_documentation(text: str, max_chars: int = 1500) -> list:
    """
    Split long documentation into smaller chunks to avoid token limits.

    Args:
        text: The documentation text to chunk
        max_chars: Maximum characters per chunk (approximate)

    Returns:
        List of text chunks
    """
    if len(text) <= max_chars:
        return [text]

    chunks = []
    # Split by paragraphs first
    paragraphs = text.split("\n\n")
    current_chunk = ""

    for paragraph in paragraphs:
        # If adding this paragraph would exceed the limit, save current chunk and start new one
        if len(current_chunk) + len(paragraph) + 2 > max_chars and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = paragraph
        else:
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph

    # Add the last chunk if it exists
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    # If any chunk is still too long, split it further
    final_chunks = []
    for chunk in chunks:
        if len(chunk) > max_chars:
            # Split long chunk into sentences
            sentences = chunk.split(". ")
            temp_chunk = ""
            for sentence in sentences:
                if len(temp_chunk) + len(sentence) + 2 > max_chars and temp_chunk:
                    final_chunks.append(temp_chunk.strip() + ".")
                    temp_chunk = sentence
                else:
                    if temp_chunk:
                        temp_chunk += ". " + sentence
                    else:
                        temp_chunk = sentence
            if temp_chunk.strip():
                final_chunks.append(temp_chunk.strip())
        else:
            final_chunks.append(chunk)

    return final_chunks


def initVanna(vn, training_data_path: str = None, db_type: str = "sqlite"):
    """
    Initialize and train a Vanna instance for SQL generation using configurable training data.

    This function configures a Vanna SQL generation agent with training data loaded from a YAML file,
    making it scalable for different SQL data sources with different contexts.
    Supports both SQLite and PostgreSQL databases.

    Args:
        vn: Vanna instance to be trained and configured
        training_data_path: Path to YAML file containing training data. If None, no training is applied.
        db_type: Database type - 'sqlite' or 'postgresql' (default: 'sqlite')

    Returns:
        None: Modifies the Vanna instance in-place

    Example:
        >>> from vanna.chromadb import ChromaDB_VectorStore
        >>> vn = NIMCustomLLM(config) & ChromaDB_VectorStore()
        >>> vn.connect_to_sqlite("path/to/database.db")
        >>> initVanna(vn, "path/to/training_data.yaml", "sqlite")
        >>> # Vanna is now ready to generate SQL queries
    """
    import os
    import logging

    logger = logging.getLogger(__name__)
    logger.info("=== Starting Vanna initialization ===")
    logger.info(f"Database type: {db_type}")

    # Get and train DDL based on database type
    if db_type == "sqlite":
        logger.info("Loading DDL from sqlite_master...")
        try:
            df_ddl = vn.run_sql("SELECT type, sql FROM sqlite_master WHERE sql is not null")
            ddl_count = len(df_ddl)
            logger.info(f"Found {ddl_count} DDL statements in sqlite_master")

            for i, ddl in enumerate(df_ddl["sql"].to_list(), 1):
                logger.debug(f"Training DDL {i}/{ddl_count}: {ddl[:100]}...")
                vn.train(ddl=ddl)

            logger.info(
                f"Successfully trained {ddl_count} DDL statements from sqlite_master"
            )
        except Exception as e:
            logger.error(f"Error loading DDL from sqlite_master: {e}")
            raise
    
    elif db_type == "postgresql":
        logger.info("Loading DDL from information_schema (PostgreSQL)...")
        try:
            # Get all tables from information_schema
            df_tables = vn.run_sql("""
                SELECT table_schema, table_name 
                FROM information_schema.tables 
                WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                AND table_type = 'BASE TABLE'
                ORDER BY table_schema, table_name
            """)
            
            table_count = len(df_tables)
            logger.info(f"Found {table_count} tables in information_schema")
            
            ddl_count = 0
            for idx, row in df_tables.iterrows():
                schema = row['table_schema']
                table = row['table_name']
                
                # Get columns for this table
                df_columns = vn.run_sql(f"""
                    SELECT 
                        column_name, 
                        data_type, 
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_schema = '{schema}' 
                    AND table_name = '{table}'
                    ORDER BY ordinal_position
                """)
                
                # Build CREATE TABLE DDL statement
                columns_ddl = []
                for _, col_row in df_columns.iterrows():
                    col_name = col_row['column_name']
                    col_type = col_row['data_type']
                    nullable = col_row['is_nullable']
                    default = col_row['column_default']
                    
                    col_def = f'"{col_name}" {col_type.upper()}'
                    if nullable == 'NO':
                        col_def += ' NOT NULL'
                    if default is not None and str(default) != 'nan':
                        col_def += f' DEFAULT {default}'
                    
                    columns_ddl.append(col_def)
                
                # Create DDL statement
                ddl = f'CREATE TABLE {schema}."{table}" (\n  ' + ',\n  '.join(columns_ddl) + '\n)'
                
                logger.debug(f"Training DDL {ddl_count + 1}/{table_count}: {schema}.{table}")
                vn.train(ddl=ddl)
                ddl_count += 1
            
            logger.info(
                f"Successfully trained {ddl_count} DDL statements from information_schema"
            )
        except Exception as e:
            logger.error(f"Error loading DDL from information_schema: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    else:
        raise ValueError(f"Unsupported database type: {db_type}. Supported types: 'sqlite', 'postgresql'")

    # Load and apply training data from YAML file
    if training_data_path:
        logger.info(f"Training data path provided: {training_data_path}")

        if os.path.exists(training_data_path):
            logger.info("Training data file exists, loading YAML...")

            try:
                import yaml

                with open(training_data_path, "r") as f:
                    training_data = yaml.safe_load(f)

                logger.info("Successfully loaded YAML training data")
                logger.info(
                    f"Training data keys: {list(training_data.keys()) if training_data else 'None'}"
                )

                # Train DDL statements
                ddl_statements = training_data.get("ddl", [])
                logger.info(f"Found {len(ddl_statements)} DDL statements")

                ddl_trained = 0
                for i, ddl_statement in enumerate(ddl_statements, 1):
                    if ddl_statement.strip():  # Only train non-empty statements
                        logger.debug(f"Training DDL {i}: {ddl_statement[:100]}...")
                        vn.train(ddl=ddl_statement)
                        ddl_trained += 1
                    else:
                        logger.warning(f"Skipping empty DDL statement at index {i}")

                logger.info(
                    f"Successfully trained {ddl_trained}/{len(ddl_statements)} DDL statements"
                )

                # Train documentation with chunking
                documentation_list = training_data.get("documentation", [])
                logger.info(f"Found {len(documentation_list)} documentation entries")

                doc_chunks = []
                for i, doc_entry in enumerate(documentation_list, 1):
                    if doc_entry.strip():
                        logger.debug(
                            f"Processing documentation entry {i}: {doc_entry[:100]}..."
                        )
                        # Chunk each documentation entry to avoid token limits
                        entry_chunks = chunk_documentation(doc_entry)
                        doc_chunks.extend(entry_chunks)
                    else:
                        logger.warning(
                            f"Skipping empty documentation entry at index {i}"
                        )

                logger.info(f"Split documentation into {len(doc_chunks)} total chunks")

                for i, chunk in enumerate(doc_chunks, 1):
                    try:
                        logger.debug(
                            f"Training documentation chunk {i}/{len(doc_chunks)} ({len(chunk)} chars)"
                        )
                        vn.train(documentation=chunk)
                    except Exception as e:
                        logger.error(f"Error training documentation chunk {i}: {e}")
                        # Continue with other chunks

                logger.info(
                    f"Successfully trained {len(doc_chunks)} documentation chunks"
                )

                # Train question-SQL pairs
                question_sql_pairs = training_data.get("sql", [])
                logger.info(f"Found {len(question_sql_pairs)} question-SQL pairs")

                pairs_trained = 0
                for i, pair in enumerate(question_sql_pairs, 1):
                    question = pair.get("question", "")
                    sql = pair.get("sql", "")
                    if question.strip() and sql.strip():  # Only train non-empty pairs
                        logger.debug(
                            f"Training question-SQL pair {i}: Q='{question[:50]}...' SQL='{sql[:50]}...'"
                        )
                        vn.train(question=question, sql=sql)
                        pairs_trained += 1
                    else:
                        if not question.strip():
                            logger.warning(
                                f"Skipping question-SQL pair {i}: empty question"
                            )
                        if not sql.strip():
                            logger.warning(f"Skipping question-SQL pair {i}: empty SQL")

                logger.info(
                    f"Successfully trained {pairs_trained}/{len(question_sql_pairs)} question-SQL pairs"
                )

                # Summary
                total_trained = ddl_trained + len(doc_chunks) + pairs_trained
                logger.info("=== Training Summary ===")
                logger.info(f"  DDL statements: {ddl_trained}")
                logger.info(f"  Documentation chunks: {len(doc_chunks)}")
                logger.info(f"  Question-SQL pairs: {pairs_trained}")
                logger.info(f"  Total items trained: {total_trained}")

            except yaml.YAMLError as e:
                logger.error(f"Error parsing YAML file {training_data_path}: {e}")
                raise
            except Exception as e:
                logger.error(
                    f"Error loading training data from {training_data_path}: {e}"
                )
                raise
        else:
            logger.warning(f"Training data file does not exist: {training_data_path}")
            logger.warning("Proceeding without YAML training data")
    else:
        logger.info("No training data path provided, skipping YAML training")

    logger.info("=== Vanna initialization completed ===")
