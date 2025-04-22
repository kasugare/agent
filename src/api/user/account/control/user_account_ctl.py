#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .control import Controller
from ..access.user_account_access import UserAccountAccess


class UserAccountController(Controller):
    def __init__(self, logger, db_conn):
        super().__init__(logger, db_conn)
        self._data_access = UserAccountAccess(logger, db_conn)

    def get_user_map(self):
        user_map_list = self._data_access.select_user_info_list()
        if user_map_list:
            user_map = user_map_list[0]
            return user_map
        return user_map_list

