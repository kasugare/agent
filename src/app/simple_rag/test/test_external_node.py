#!/usr/bin/env python
# -*- coding: utf-8 -*-


class ExternalRPC:
    def __init__(self, logger, embedding_server_path, embed_model_nm, vectordb_type, vectordb_path, test_env_key):
        self._logger = logger
        self._embedding_server_path = embedding_server_path
        self._embed_model_nm = embed_model_nm
        self._vectordb_type = vectordb_type
        self._vectordb_path = vectordb_path
        self._test_env_key = test_env_key

    async def test_service(self, query):
        self._logger.critical(f"environment variable assigned test")
        self._logger.critical(f"  - {self._embedding_server_path}")
        self._logger.critical(f"  - {self._embed_model_nm}")
        self._logger.critical(f"  - {self._vectordb_type}")
        self._logger.critical(f"  - {self._vectordb_path}")
        self._logger.critical(f"  - {self._test_env_key}")
        return self._embedding_server_path, self._embed_model_nm, self._vectordb_type, self._vectordb_path, self._test_env_key