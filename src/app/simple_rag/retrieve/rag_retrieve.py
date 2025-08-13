#!/usr/bin/env python
# -*- coding: utf-8 -*-

from langchain_openai import OpenAIEmbeddings
from .vectordb_loader import VectorDBLoader


class RagRetrieve:
    def __init__(self, logger):
        self._logger = logger

    async def retrieve(self, query, top_k):
        embedding_server_path = "http://192.15.90.108:21434/v1"
        embed_model_nm = "nomic-embed-text:latest"
        vectordb_type = "qdrant"
        vectordb_path = "http://192.15.90.108:31633"
        collection_name = "agent"
        api_key = "dummy"

        embedding_model = OpenAIEmbeddings(openai_api_base=embedding_server_path, model=embed_model_nm, api_key=api_key, check_embedding_ctx_length=False)

        vector_db_loader = VectorDBLoader(self._logger)
        vector_db = vector_db_loader.load(
            db_type=vectordb_type,
            connection_string=vectordb_path,
            collection_name=collection_name,
            embedding_model=embedding_model
        )

        documents = await vector_db.search(query=query, top_k=top_k)
        retrieved_documents = [doc["text"] for doc in documents]
        document_sources = [doc["metadata"] for doc in documents]

        self._logger.critical(retrieved_documents)
        return retrieved_documents, document_sources