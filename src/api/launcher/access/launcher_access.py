# -*- coding: utf-8 -*-
#!/usr/bin/env python

from ailand.dao.aidao import Access
from .query_pool import *
import traceback


class LauncherAccess(Access):
    def __init__(self, logger, db_conn):
        super().__init__(logger, db_conn)

    def get_init_service_data(self):
        query_string = select_init_service_module_query()
        data_list = self.execute_get(query_string)
        return data_list
