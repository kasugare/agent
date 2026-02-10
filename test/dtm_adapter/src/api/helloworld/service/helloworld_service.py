#!/usr/bin/env python
# -*- code utf-8 -*-

from ailand.dao.aidao import Service
from pymysql import Connection

from api.helloworld.controller.helloworld_controller import HelloWorldController


class HelloWorldService(Service):
    def __init__(self, logger, db_conn: Connection):
        super().__init__(logger, db_conn)
        self._logger = logger
        self._db_conn = db_conn

        self._helloworld_controller = HelloWorldController(logger, db_conn)

    def greet(self, name_dict: dict):
        _name = name_dict['name']
        greeting = f"Hello world, {_name}!"
        return greeting
