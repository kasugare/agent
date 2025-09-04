#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Retrieval:
    def __init__(self, collection_id: int):
        self._collection_id = collection_id

    def retrieve_documents(self, query: str) -> dict:
        result = {
            "retrieved_documents": "result: retrieved_documents",
            "document_sources": "result: document_sources",
            "document_meta": "result: document_meta"
        }
        return result