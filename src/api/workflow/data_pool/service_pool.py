#!/usr/bin/env python
# -*- coding: utf-8 -*-

class ServicePool:
    # _instance = None
    #
    # def __new__(cls, *args, **kwargs):
    #     if cls._instance is None:
    #         cls._instance = super().__new__(cls)
    #     return cls._instance

    def __init__(self, logger):
        self._logger = logger
        self._service_pool = {}

    def create_service_instance(self, service_key, service_instance):
        if service_key in self._service_pool.keys():
            self._logger.warn(f"already exist service_key: {service_key}")
        instance = service_instance(self._logger, service_key)
        self._service_pool[service_key] = instance
        return service_key, instance

    def set_service_instance(self, service_key, instance):
        self._service_pool[service_key] = instance

    def get_service_instance(self, service_key):
        service_instance = self._service_pool.get(service_key, None)
        if not service_instance:
            self._logger.warn(f"not exist store_key in service_store: {service_key}")
        return service_instance

    def get_service_pool(self):
        return self._service_pool

    def service_keys(self):
        store_keys = list(self._service_pool.keys())
        return store_keys

    def del_service_instance(self, service_key):
        try:
            service_instance = self.get_service_instance(service_key)
            if service_instance:
                del self._service_pool[service_key]
        except Exception as e:
            self._logger.error(e)

    def clear(self):
        self._service_pool.clear()