#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.launcher.router.service.launcher_service import DynamicRouterService
from api.launcher.route_meta.service.route_meta_service import RouteMetaService
from common.conf_system import getRouteDirPath, getRouteFileName, getLaucherApis, isServiceMetaReload, getLockDir
from abc import ABC, abstractmethod
from fastapi import APIRouter, FastAPI
from watchfiles import awatch
import asyncio
import traceback
import json
import os


class BaseHandler:
    def __init__(self, app: FastAPI, logger):
        self.app = app
        self._logger = logger
        self._route_meta_service = RouteMetaService(logger)

        self.dynamic_router = DynamicRouterService(logger, app)
        self.router = APIRouter(tags=['ADMIN'])
        self.setup_routes()

        route_dir_path = getRouteDirPath()
        route_file_name = getRouteFileName()
        self._routes_file_path = f"{route_dir_path}/{route_file_name}"
        self._init_service_path(route_dir_path)

        # FastAPI 시작 시 파일 감시 시작
        @app.on_event("startup")
        async def startup_event():
            if isServiceMetaReload():
                asyncio.create_task(self._watch_routes())
                self._init_runtime_service()
            else:
                await self._sync_routes()

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
            try:
                self._route_meta_service.set_route_meta(**service_api_info)
            except Exception as e:
                self._logger.error(e)
                self._logger.error(f"{service_api_info}")
        self._add_service_router()

    async def _watch_routes(self):
        self._logger.debug(f"watch changeable route-path: routes.json")
        try:
            async for changes in awatch(self._routes_file_path):
                await self._sync_routes()
        except Exception as e:
            self._logger.error(traceback.format_exc())
            self._logger.warn(f"Not ready {self._routes_file_path} file")

    async def _sync_routes(self):
        if not os.path.exists(self._routes_file_path):
            return
        self._add_service_router()

    def _add_service_router(self):
        active_services = getLaucherApis()
        try:
            route_info = self._route_meta_service.get_route_meta()
            for service_name, module_info in route_info.items():
                if "*" in active_services:
                    pass
                elif service_name not in active_services:
                    continue
                self._logger.debug(f"service_name: {service_name}")
                prefix = module_info.get('prefix')
                module_name = module_info.get('module_name')
                class_name = module_info.get('class_name')
                self.dynamic_router.add_api_service(prefix, module_name, class_name)
        except json.JSONDecodeError:
            self._logger.error("Invalid routes file format")

    async def add_api_service(self, prefix, module_name, class_name):
        self.dynamic_router.add_api_service(prefix, module_name, class_name)
        self._route_meta_service.set_route_meta(prefix, module_name, class_name)

    @abstractmethod
    def setup_routes(self):
        pass

    def get_app(self):
        return self.app

    def get_router(self) -> APIRouter:
        return self.router

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
            await self.add_api_service(prefix, module_name, class_name)
            self.reset_openapi()
            return {"prefix": prefix, "module_name": module_name, "class_name": class_name}

        @self.router.post("/del")
        async def del_service(prefix, route_path):
            # prefix = "/api/v1"
            # path = "/user/add"
            self.dynamic_router.del_app_router(prefix, route_path)
            self.reset_openapi()
