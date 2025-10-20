#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ailand.dao.aidao import Controller
from ..access.launcher_access import LauncherAccess


class LauncherController(Controller):
    def __init__(self, logger, db_conn):
        super().__init__(logger, db_conn)
        self._launcher_access = LauncherAccess(logger, db_conn)

    def get_init_service_meta(self):
        init_service_meta = self._launcher_access.get_init_service_data()
        return init_service_meta