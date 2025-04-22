#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .service import Service
from ..control.user_account_ctl import UserAccountController


class UserAccountService(Service):
    def __init__(self, logger, db_conn):
        super().__init__(logger, db_conn)
        self._logger = logger
        self._indexCount = 0
        self.db_conn = db_conn

        self._controller = UserAccountController(logger, db_conn)

    def get_user_info(self):
        userInfoMap = self._controller.get_user_map()
        return userInfoMap
