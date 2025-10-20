#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Retrieval:
    def __init__(self, collection_id: int):
        self._collection_id = collection_id

    def retrieve_documents(self, query: str) -> dict:
        result = {
            "retrieved_documents": ["document_1", "document_2", "document_3"],
            "document_sources": ["source_1", "source_2"],
            "document_meta": "document_meta"
        }
        return result