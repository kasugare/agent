#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.launcher.router.access.launcher_access import LauncherAccess
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

class LauncherController(Controller):
    def __init__(self, logger, db_conn):
        super().__init__(logger, db_conn)
        self._launcher_access = LauncherAccess(logger, db_conn)

    def get_init_service_meta(self):
        init_service_meta = self._launcher_access.get_init_service_data()
        return init_service_meta