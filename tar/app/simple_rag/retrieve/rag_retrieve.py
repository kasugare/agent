#!/usr/bin/env python
# -*- coding: utf-8 -*-

from langchain_openai import OpenAIEmbeddings
from .vectordb_loader import VectorDBLoader

class RagRetrieve:
    def __init__(self, logger, asset_info={}):
        self._logger = logger
        self._vector_db_loader = None
        self._vector_db = None
        self._set_asset(**asset_info)

    def _set_asset(self, knowledge_id, embedding_server_path, embed_model_nm, vectordb_type, vectordb_path, api_key=None):
        self._knowledge_id = knowledge_id
        self._embedding_server_path = embedding_server_path
        self._embed_model_nm = embed_model_nm
        self._vectordb_type = vectordb_type
        self._vectordb_path = vectordb_path
        self._api_key = api_key

    async def retrieve(self, query, top_k, check_embedding_ctx_length=False, threshold=0.1):
        # collection_name: as vectorDB's table == knowledge name
        # check_embedding_ctx_length: ??

        embedding_model = OpenAIEmbeddings(openai_api_base=self._embedding_server_path, model=self._embed_model_nm, api_key=self._api_key, check_embedding_ctx_length=check_embedding_ctx_length)
        if not self._vector_db:
            vector_db_loader = VectorDBLoader(self._logger)
            self._vector_db = vector_db_loader.load(
                db_type=self._vectordb_type,
                connection_string=self._vectordb_path,
                collection_name=self._knowledge_id,
                embedding_model=embedding_model
            )

        documents = await self._vector_db.search(query=query, top_k=top_k, score_threshold=threshold)
        retrieved_documents = [doc["text"] for doc in documents]
        document_sources = [doc["metadata"] for doc in documents]

        self._logger.critical(retrieved_documents)
        return retrieved_documents, document_sources