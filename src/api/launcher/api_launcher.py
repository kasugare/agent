#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .service.launcher_service import DynamicRouterService
from .utility.file_lock import FileLock
from common.conf_system import getLockDir, getRouteDir, getAiLandContext
from abc import ABC, abstractmethod
from fastapi import APIRouter, FastAPI
from watchfiles import awatch
import asyncio
import traceback
import pymysql
import json
import os


class BaseHandler:
    def __init__(self, app: FastAPI, logger):
        self.app = app
        self._logger = logger
        self._db_conn = self._set_db_conn()

        self.dynamic_router = DynamicRouterService(app, logger, self._db_conn)
        self.router = APIRouter(tags=['ADMIN'])
        self.setup_routes()

        route_dir_path = getRouteDir()
        self._routes_file_path = f"{route_dir_path}/api_routes.json"
        self._init_service_path(route_dir_path)

        # FastAPI 시작 시 파일 감시 시작
        @app.on_event("startup")
        async def startup_event():
            asyncio.create_task(self._watch_routes())

        self._init_runtime_service()

    def _init_service_path(self, route_dir_path):
        if not os.path.exists(route_dir_path):
            try:
                os.mkdir(route_dir_path)
            except Exception as e:
                self._logger.error(e)

        if not os.path.exists(self._routes_file_path):
            try:
                with open(self._routes_file_path, 'w') as f:
                    json.dump({}, f, indent=2)
            except Exception as e:
                self._logger.error(e)

    def _init_runtime_service(self):
        init_service_api_info = self.dynamic_router.get_init_service_info()
        for service_api_info in init_service_api_info:
            self._set_service_info(**service_api_info)
        self._add_service_router()

    async def _watch_routes(self):
        self._logger.debug(f"watch changeable route-path: routes.json")
        try:
            async for changes in awatch(self._routes_file_path):
                await self._sync_routes()
        except Exception as e:
            self._logger.error(traceback.format_exc())
            self._logger.warn(f"Not ready {self._routes_file_path} file")

    def _add_service_router(self):
        with FileLock(f"{getLockDir()}/routes.lock"):
            with open(self._routes_file_path, 'r') as fd:
                try:
                    route_info = json.load(fd)
                    for class_name, module_info in route_info.items():
                        self._logger.debug(f"class_name: {class_name}")
                        prefix = module_info.get('prefix')
                        module_name = module_info.get('module_name')
                        class_name = module_info.get('class_name')
                        self.dynamic_router.add_api_service(prefix, module_name, class_name)
                except json.JSONDecodeError:
                    self._logger.error("Invalid routes file format")

    async def _sync_routes(self):
        if not os.path.exists(self._routes_file_path):
            return
        self._add_service_router()

    def _set_service_info(self, prefix, module_name, class_name):
        if os.path.exists(self._routes_file_path):
            with FileLock(f"{getLockDir()}/routes.lock"):
                with open(self._routes_file_path, 'r') as f:
                    try:
                        service_info = json.load(f)
                    except json.JSONDecodeError:
                        service_info = {}

                service_info[class_name] = {
                    'prefix': prefix,
                    'module_name': module_name,
                    'class_name': class_name
                }

                with open(self._routes_file_path, 'w') as fd:
                    json.dump(service_info, fd, indent=2)

    async def add_api_service(self, prefix, module_name, class_name):
        self.dynamic_router.add_api_service(prefix, module_name, class_name)
        self._set_service_info(prefix, module_name, class_name)

    def _set_db_conn(self):
        dbConn = None
        dbContext = getAiLandContext()

        try:
            dbConn = pymysql.connect(host=dbContext['host']
                                     , port=dbContext['port']
                                     , user=dbContext['user']
                                     , passwd=dbContext['passwd']
                                     , db=dbContext['db']
                                     , cursorclass=pymysql.cursors.DictCursor
                                     , autocommit=True)
        except Exception as e:
            self._logger.error(traceback.format_exc())
        return dbConn

    def set_logger(self):
        # logger = logging.getLogger()
        logger = None
        return logger

    @abstractmethod
    def setup_routes(self):
        pass

    def get_app(self):
        return self.app

    def get_router(self) -> APIRouter:
        return self.router

    def get_launcher_service(self) -> DynamicRouterService:
        return self.dynamic_router

    def get_db_conn(self):
        if not self._db_conn:
            self._db_conn = self._set_db_conn()
        return self._db_conn

    def reset_openapi(self):
        self.app.openapi_schema = None
        self.app.openapi()


class ApiLauncher(BaseHandler):
    def __init__(self, app: FastAPI, logger):
        super().__init__(app, logger)
        self._logger = logger

    def setup_routes(self):
        @self.router.post("/add")
        async def add_service(prefix, module_name, class_name) -> dict:
            # prefix = "/api/v1"
            # module_name = "api.serving.serving_api"
            # class_name = "ServingProvider"

            await self.add_api_service(prefix, module_name, class_name)
            self.reset_openapi()
            return {"prefix": prefix, "module_name": module_name, "class_name": class_name}

        @self.router.post("/del")
        async def del_service(prefix, route_path):
            # prefix = "/api/v1"
            # path = "/user/add"
            self.dynamic_router.del_app_router(prefix, route_path)
            self.reset_openapi()
