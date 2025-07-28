#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.error_pool.error import NotExistedData
from copy import deepcopy
import traceback
import threading

class CachedIODataAccess:
    def __init__(self, logger):
        self._logger = logger

        self._thread_lock = threading.Lock()
        # self._service_data_pool = {}
        self._data_pool = {}

    def get_data(self, key):
        value = None
        try:
            self._thread_lock.acquire()
            value = self._data_pool[key]
        except KeyError as e:
            self._logger.error(e)
            raise NotExistedData
        except Exception as e:
            self._logger.error(e)
        finally:
            self._thread_lock.release()
        return value

    def get_all(self):
        self._thread_lock.acquire()
        data = deepcopy(self._data_pool)
        self._thread_lock.release()
        return data

    def set_data(self, value_id, data):
        self._thread_lock.acquire()
        self._data_pool[value_id] = data
        self._thread_lock.release()

    def delete(self, service_id):
        try:
            self._thread_lock.acquire()
            target_keys = [key for key, _ in self._data_pool.items() if key.find(service_id) == 0]
            for key in target_keys:
                del self._data_pool[key]
        except KeyError as e:
            pass
        except Exception as e:
            self._logger.error(e)
            traceback.print_exc()
        finally:
            self._thread_lock.release()

    def clean(self):
        try:
            self._thread_lock.acquire()
            self._data_pool.clear()
        except AttributeError as e:
            self._data_pool = {}
        except Exception as e:
            self._logger.error(e)
        finally:
            self._thread_lock.release()