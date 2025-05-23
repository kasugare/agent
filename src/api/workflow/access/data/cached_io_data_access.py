#!/usr/bin/env python
# -*- coding: utf-8 -*-

from copy import deepcopy
import traceback
import threading

class CachedIODataAccess:
    def __init__(self, logger):
        self._logger = logger

        self._thread_lock = threading.Lock()
        self._data_pool = {}

    def get(self, service_id: str):
        self._thread_lock.acquire()
        data = self._data_pool.get(service_id)
        self._thread_lock.release()
        return data

    def get_all(self):
        self._thread_lock.acquire()
        data = deepcopy(self._data_pool)
        self._thread_lock.release()
        return data

    def set(self, service_id, data):
        self._thread_lock.acquire()
        self._data_pool[service_id] = data
        self._thread_lock.release()

    def update(self, service_id, data):
        self._thread_lock.acquire()
        self._data_pool.update(service_id, data)
        self._thread_lock.release()

    def delete(self, service_id):
        try:
            self._thread_lock.acquire()
            del self._data_pool[service_id]
            self._thread_lock.release()
        except Exception as e:
            self._logger.error(traceback.print_exc(e))

    def clean(self):
        self._thread_lock.acquire()
        self._data_pool.clear()
        self._thread_lock.release()