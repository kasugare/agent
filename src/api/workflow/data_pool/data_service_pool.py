#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.data_pool.service_pool import ServicePool
from api.workflow.service.data.data_store_service import DataStoreService


class DataServicePool(ServicePool):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, logger):
        super().__init__(logger)
        self._logger = logger

    def _gen_store_key(self, workflow_id, session_id, request_id):
        store_key = f"{workflow_id}-{session_id}-{request_id}"
        return store_key

    def create_pool(self, workflow_id, session_id, request_id):
        store_key = self._gen_store_key(workflow_id, session_id, request_id)
        service_key, instance = self.create_service_instance(store_key, DataStoreService)
        return service_key, instance

    def get_datastore(self, store_key):
        data_store = self.get_service_instance(store_key)
        return data_store

    def get_service_map(self):
        return self.get_service_pool()

    def del_datastore(self, store_key):
        self.del_service_instance(store_key)
