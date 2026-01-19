#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.data_pool.service_pool import ServicePool
from api.workflow.service.data.meta_store_service import MetaStoreService


class MetaServicePool(ServicePool):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, logger):
        super().__init__(logger)
        self._logger = logger

    def create_pool(self, workflow_id):
        service_key, metastore_service = self.create_service_instance(workflow_id, MetaStoreService)
        return service_key, metastore_service

    def set_metastore(self, workflow_id, metastore):
        self.set_service_instance(workflow_id, metastore)

    def get_metastore(self, workflow_id):
        metastore_service = self.get_service_instance(workflow_id)
        return metastore_service

    def del_metastore(self, workflow_id):
        self.del_service_instance(workflow_id)
