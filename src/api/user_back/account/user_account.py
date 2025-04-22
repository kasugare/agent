#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .service.user_account_service import UserAccountService
from fastapi import APIRouter, FastAPI
from abc import ABC, abstractmethod
from typing import List
import traceback
import pymysql


class BaseRouter:
    def __init__(self):
        self.router = APIRouter(tags=["USER"])
        self.setup_routes()

    @abstractmethod
    def setup_routes(self):
        # 이 메서드를 오버라이드하여 라우트를 정의합니다
        pass

    def get_router(self) -> APIRouter:
        return self.router


class UserAccountRouter(BaseRouter):
    def __init__(self, logger, db_conn):
        super().__init__()
        self._logger = logger
        self._service = UserAccountService(logger, db_conn)


    def setup_routes(self):
        @self.router.get(path='/user')
        async def get_items1() -> List[dict]:
            import time
            time.sleep(15)
            return [{"id": '/user', "name": "Item 1"}]

        @self.router.get(path='/user/info')
        async def get_user_info() -> List[dict]:
            user_info_map = self._service.get_user_info()
            return [{"id": '/user/info', "name": "Item 1"}, user_info_map]

        @self.router.get(path='/user/add')
        async def get_items2() -> List[dict]:
            return [{"id": '/user/add', "name": "Item 1"}]

        @self.router.get(path='/user/update')
        async def get_items3() -> List[dict]:
            return [{"id": '/user/update', "name": "Item 1"}]

        @self.router.get(path='/user/del')
        async def get_items4() -> List[dict]:
            return [{"id": '/user/del', "name": "Item 1"}]
