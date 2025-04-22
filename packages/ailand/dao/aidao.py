#!/usr/bin/env python
# -*- coding: utf-8 -*-


import traceback
import time


class Service:
    def __init__(self, logger, db_conn):
        self._logger = logger
        self.db_conn = db_conn


class Controller:
    def __init__(self, logger=None, db_conn=None):
        self._logger = logger
        self._db_conn = db_conn

    def gen_user_id(self) -> str:
        ts = int(time.time() * 10000000)
        id = "%14X" %ts
        return id

    def gen_id_len_10(self) -> str:
        ts = int(time.time() * 10000000)
        id = "%10X" % ts
        return id


class Access:
    def __init__(self, logger, db_conn):
        self._logger = logger
        self._db_conn = db_conn

    def __del__(self):
        if self._db_conn:
            self._close()

    def _close(self):
        try:
            self._db_conn.close()
        except Exception as e:
            print(traceback.format_exc())

    def _getCursor(self):
        try:
            cursor = self._db_conn.cursor()
            return cursor
        except Exception as e:
            print(traceback.format_exc())

    def execute_get(self, query_string):
        resultList = None
        try:
            cursor = self._getCursor()
            cursor.execute(query_string)
            resultList = cursor.fetchall()
        except Exception as e:
            print(traceback.format_exc())
        return resultList

    def execute_set(self, query_string):
        result = None
        try:
            cursor = self._getCursor()
            result = cursor.execute(query_string)
        except Exception as e:
            print(traceback.format_exc())
        return result

    def execute_set_many(self, query_string, data_set):
        result = None
        try:
            cursor = self._getCursor()
            result = cursor.executemany(query_string, data_set)
        except Exception as e:
            print(traceback.format_exc())
        return result
