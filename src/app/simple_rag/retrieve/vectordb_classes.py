#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib.parse
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from langchain.embeddings.base import Embeddings
from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, Filter, FieldCondition, MatchValue


class BaseVectorDB(ABC):
    """Base class for LangChain vector database integrations."""

    def __init__(self, logger, connection_string: str, embedding_model: Optional[Embeddings] = None):
        """
        Initialize the base vector database.

        Args:
            connection_string: Path or URL to the vector database
            embedding_model: LangChain embeddings model (defaults to HuggingFace if None)
        """
        self._logger = logger
        self.connection_string = connection_string
        self.is_url = self._is_url(connection_string)
        self.embedding_model = embedding_model or HuggingFaceEmbeddings()
        self.vectorstore = None

    def _is_url(self, connection_string: str) -> bool:
        """Check if the connection string is a URL."""
        try:
            result = urllib.parse.urlparse(connection_string)
            return all([result.scheme, result.netloc])
        except:
            return False

    def _get_dimension(self) -> int:
        """Check if the connection string is a URL."""
        vector_size = len(self.embedding_model.embed_query("sample text"))
        return vector_size

    @abstractmethod
    def connect(self) -> bool:
        """Connect to the vector database."""
        pass

    def add_documents(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """
        Add documents to the vector database.

        Args:
            texts: List of document texts
            metadatas: Optional metadata for each document

        Returns:
            List of document IDs
        """
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Call connect() first.")

        # Create Document objects
        documents = []
        for i, text in enumerate(texts):
            metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
            documents.append(Document(page_content=text, metadata=metadata))

        # Add documents to vectorstore
        try:
            ids = self.vectorstore.add_documents(documents)
            return ids
        except Exception as e:
            self._logger.error(f"Error adding documents: {e}")
            return []

    def _get_filter_condition(self) -> dict:
        # VectorDB에 설정된 값을 기반으로 조건절에서 사용
        filter_condition = {
            "should": [
                {
                    "key": "use_yn",
                    "match": {
                        "value": "Y"
                    }
                },
                {
                    "key": "use_yn",
                    "is_empty": True
                }
            ]
        }
        return filter_condition

    async def search(self, query: str, top_k: int=5, exclude_pages: list[int]=None, score_threshold: float=0.1) -> List[Dict[str, Any]]:
        """
        Search for similar documents.

        Args:
            query: Query string
            top_k: Number of results to return
            exclude_pages : search filter

        Returns:
            List of similar documents with metadata and scores
        """
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Call connect() first.")

        try:
            # if exclude_pages is not None:
            #     exclude_filter = self.build_page_not_in_filter(exclude_pages=exclude_pages)
            #     results = self.vectorstore.similarity_search_with_score(query, k=top_k, filter=exclude_filter)
            # else:
            filter_condition = self._get_filter_condition()
            results = await self.vectorstore.asimilarity_search_with_score(query, k=top_k, score_threshold=score_threshold, filter=filter_condition)
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    'text': doc.page_content,
                    'metadata': doc.metadata,
                    'score': score
                })
            return formatted_results
        except Exception as e:
            self._logger.error(f"Error searching documents: {e}")
            return []

    @abstractmethod
    def delete(self, document_ids: List[str]) -> bool:
        """
        Delete documents from the database.

        Args:
            document_ids: List of document IDs to delete

        Returns:
            Success status
        """
        pass

    def disconnect(self) -> bool:
        """Disconnect from the database."""
        self.vectorstore = None
        return True

    def build_page_not_in_filter(self, exclude_pages):
        pass


class QdrantDB(BaseVectorDB):
    """Qdrant implementation using LangChain."""

    def __init__(self, logger, connection_string: str, collection_name: str = "default_collection",
                 embedding_model: Optional[Embeddings] = None):
        """
        Initialize Qdrant with LangChain.

        Args:
            connection_string: URL or path to Qdrant
            collection_name: Name of the collection
            embedding_model: LangChain embeddings model
        """
        super().__init__(logger, connection_string, embedding_model)
        self.collection_name = collection_name

    def connect(self) -> bool:
        """Connect to Qdrant."""
        try:

            if self.is_url:
                # Parse URL for remote Qdrant
                parsed_url = urllib.parse.urlparse(self.connection_string)
                host = parsed_url.hostname
                port = parsed_url.port or 6333

                # Check for API key in query parameters
                query_params = urllib.parse.parse_qs(parsed_url.query)
                api_key = query_params.get('api_key', [None])[0]

                # Configure Qdrant client
                client = QdrantClient(host=host, port=port, api_key=api_key)

                # Check if collection exists
                collections = client.get_collections().collections
                collection_names = [collection.name for collection in collections]

                # Create collection if it doesn't exist
                if self.collection_name not in collection_names:
                    # 차원 수 확인
                    # vector_size = len(self.embedding_model.embed_query("sample text"))

                    client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(size=self._get_dimension(), distance=Distance.COSINE)
                    )

                    self._logger.info(f"Created new collection '{self.collection_name}' in Qdrant")

                # Initialize vector store
                self.vectorstore = Qdrant(
                    client=client,
                    collection_name=self.collection_name,
                    embeddings=self.embedding_model
                )
            else:
                # For local Qdrant
                path = self.connection_string
                client = QdrantClient(path=path)

                # Check if collection exists
                collections = client.get_collections().collections
                collection_names = [collection.name for collection in collections]

                # Create collection if it doesn't exist
                if self.collection_name not in collection_names:
                    client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
                    )

                    self._logger.info(f"Created new collection '{self.collection_name}' in Qdrant")

                self.vectorstore = Qdrant(
                    client=client,
                    collection_name=self.collection_name,
                    embeddings=self.embedding_model
                )

            return True
        except Exception as e:
            self._logger.error(f"Failed to connect to Qdrant: {e}")
            return False

    def delete(self, document_ids: List[str]) -> bool:
        """Delete documents from Qdrant."""
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Call connect() first.")

        try:
            # Access the underlying Qdrant client
            client = self.vectorstore._client

            # Delete points by IDs
            client.delete(
                collection_name=self.collection_name,
                points_selector=document_ids
            )

            return True
        except Exception as e:
            self._logger.error(f"Error deleting documents from Qdrant: {e}")
            return False

    def build_page_not_in_filter(self, exclude_pages: list[int]) -> Filter:
        must_not_conditions = []
        for page in exclude_pages:
            must_not_conditions.append(
                FieldCondition(
                    key="metadata.page",
                    match=MatchValue(value=page)
                )
            )
        return Filter(must_not=must_not_conditions)
