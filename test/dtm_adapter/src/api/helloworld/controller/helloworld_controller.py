#!/usr/bin/env python
# -*- code utf-8 -*-

from ailand.dao.aidao import Controller
from pymysql import Connection

from api.helloworld.access.helloworld_access import HelloWorldAccess


class HelloWorldController(Controller):
    def __init__(self, logger, db_conn: Connection):
        super().__init__(logger, db_conn)
        self._logger = logger
        self._db_conn = db_conn

        self._user_info_access = HelloWorldAccess(logger, db_conn)
