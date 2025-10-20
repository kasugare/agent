# -*- coding: utf-8 -*-
#!/usr/bin/env python

from .access import Access
from .query_pool import *
import traceback


class UserAccountAccess(Access):
    def __init__(self, logger, db_conn):
        super().__init__(logger, db_conn)

    def select_user_info_list(self):
        query_string = select_user_info_query()
        data_list = self.execute_get(query_string)
        return data_list
