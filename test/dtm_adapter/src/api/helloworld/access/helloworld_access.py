#!/usr/bin/env python
# -*- code utf-8 -*-
from ailand.dao.aidao import Access
from pymysql import Connection


class HelloWorldAccess(Access):
    def __init__(self, logger, db_conn: Connection):
        super().__init__(logger, db_conn)
        self._logger = logger
        self._db_conn = db_conn
