#!/usr/bin/env python
# -*- coding: utf-8 -*-

from langchain_openai import OpenAIEmbeddings
from .vectordb_loader import VectorDBLoader

class RagRetrieve:
    def __init__(self, logger, embedding_server_path, embed_model_nm, vectordb_type, vectordb_path, api_key=None):
        self._logger = logger
        self._vector_db_loader = None
        self._vector_db = None
        self._api_key = api_key
        self._embedding_server_path = embedding_server_path
        self._embed_model_nm = embed_model_nm
        self._vectordb_type = vectordb_type
        self._vectordb_path = vectordb_path

    async def retrieve(self, query, top_k, collection_name, check_embedding_ctx_length=False):
        embedding_model = OpenAIEmbeddings(openai_api_base=self._embedding_server_path, model=self._embed_model_nm, api_key=self._api_key, check_embedding_ctx_length=check_embedding_ctx_length)
        if not self._vector_db:
            vector_db_loader = VectorDBLoader(self._logger)
            self._vector_db = vector_db_loader.load(
                db_type=self._vectordb_type,
                connection_string=self._vectordb_path,
                collection_name=collection_name,
                embedding_model=embedding_model
            )

        documents = await self._vector_db.search(query=query, top_k=top_k)
        retrieved_documents = [doc["text"] for doc in documents]
        document_sources = [doc["metadata"] for doc in documents]

        self._logger.critical(retrieved_documents)
        return retrieved_documents, document_sources