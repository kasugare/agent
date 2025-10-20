#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .vectordb_classes import BaseVectorDB, QdrantDB
from langchain.embeddings.base import Embeddings
from typing import Dict, Optional, Type
import importlib


class VectorDBLoader:
    """
    A loader class for LangChain vector databases.
    Supports ChromaDB, FAISS, and Qdrant through LangChain integrations.
    """

    # Mapping of DB types to their respective LangChain classes
    _DB_TYPES = {
        'qdrant': QdrantDB
    }
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, logger):
        """Initialize the loader."""
        self._logger = logger

    def check_dependencies(self, db_type: str) -> bool:
        """
        Check if the required dependencies for a specific DB type are installed.

        Args:
            db_type: Type of vector database ('chromadb', 'faiss', 'qdrant')

        Returns:
            True if dependencies are installed, False otherwise
        """
        try:
            if db_type == 'qdrant':
                importlib.import_module('qdrant_client')
                importlib.import_module('langchain.vectorstores.qdrant')
            else:
                return False

            return True
        except ImportError:
            self._logger.error(f"Missing dependencies for {db_type}")
            return False

    def load(self,
             db_type: str,
             connection_string: str,
             collection_name: Optional[str] = None,
             embedding_model: Optional[Embeddings] = None,
             **kwargs) -> Optional[BaseVectorDB]:
        """
        Load a LangChain vector database.

        Args:
            db_type: Type of vector database ('chromadb', 'faiss', 'qdrant')
            connection_string: File path or URL to the database
            collection_name: Name of the collection (for ChromaDB and Qdrant)
            embedding_model: LangChain embedding model to use
            **kwargs: Additional parameters for the specific DB type

        Returns:
            Initialized VectorDB instance or None if loading fails
        """
        # Check if the DB type is supported
        if db_type.lower() not in self._DB_TYPES:
            self._logger.error(f"Unsupported vector database type: {db_type}")
            return None

        # Check if dependencies are installed
        if not self.check_dependencies(db_type.lower()):
            self._logger.error(f"Missing dependencies for {db_type}")
            return None

        try:
            # Get the appropriate class for the DB type
            db_class = self._DB_TYPES[db_type.lower()]

            # Initialize the DB instance with the appropriate parameters
            if db_type.lower() in ['qdrant'] and collection_name:
                db = db_class(
                    logger=self._logger,
                    connection_string=connection_string,
                    collection_name=collection_name,
                    embedding_model=embedding_model,
                    **kwargs
                )
            else:
                db = db_class(
                    connection_string=connection_string,
                    embedding_model=embedding_model,
                    **kwargs
                )

            # Connect to the database
            success = db.connect()

            if success:
                self._logger.info(f"Successfully connected to {db_type} at {connection_string}")
                return db
            else:
                self._logger.error(f"Failed to connect to {db_type} at {connection_string}")
                return None

        except Exception as e:
            self._logger.error(f"Error loading {db_type} model: {e}")
            return None

    def get_available_db_types(self) -> Dict[str, bool]:
        """
        Get a list of available vector database types and their dependency status.

        Returns:
            Dictionary of DB types and whether their dependencies are installed
        """
        return {db_type: self.check_dependencies(db_type) for db_type in self._DB_TYPES}

    def get_embedding_models(self) -> Dict[str, Type[Embeddings]]:
        """
        Get available embedding models from LangChain.

        Returns:
            Dictionary of embedding model names and their classes
        """
        try:
            from langchain_community.embeddings import (
                HuggingFaceEmbeddings,
                OpenAIEmbeddings,
                CohereEmbeddings
            )

            return {
                'huggingface': HuggingFaceEmbeddings,
                'openai': OpenAIEmbeddings,
                'cohere': CohereEmbeddings
            }
        except ImportError:
            self._logger.warning("Some embedding models might not be available")
            return {}
