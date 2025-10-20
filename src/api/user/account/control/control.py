#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time


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

