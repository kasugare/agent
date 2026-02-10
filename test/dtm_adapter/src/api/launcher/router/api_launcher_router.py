#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import List

from ailand.common import database
from ailand.common.database import db_conn as get_db_conn
from ailand.router.airouter import BaseRouter
from fastapi import FastAPI, Depends
from fastapi.routing import APIRoute
from pymysql import Connection

from api.launcher.schema.launcher_schema import ResModelOfAPIRoutes, ReqModelOfAddServicePackage, ReqModelOfDeleteServicePackage
from api.launcher.service.launcher_service import ServiceLauncher


class ApiLauncher(BaseRouter):

    def __init__(self, app: FastAPI):
        super().__init__(tags=["ADMIN"])
        self.app = app

    def get_app(self):
        return self.app

    def reset_openapi(self):
        self.app.openapi_schema = None
        self.app.openapi()

    def parse_route(self, route: APIRoute) -> ResModelOfAPIRoutes:
        response = ResModelOfAPIRoutes(
            path=route.path,
            name=route.name,
            methods=list(route.methods),
            function=route.endpoint.__name__
        )
        return response

    def get_all_routes(self) -> List[ResModelOfAPIRoutes]:
        routes = []
        for route in self.app.routes:
            if isinstance(route, APIRoute):
                routes.append(self.parse_route(route))
        return routes

    def setup_routes(self):
        @self.router.post("/service-package/add", response_model=List[ResModelOfAPIRoutes])
        async def add_service_package(request: ReqModelOfAddServicePackage, db_conn: Connection = Depends(get_db_conn)):
            launcher_service = ServiceLauncher(self.app, self._logger, db_conn)
            launcher_service.load_service_package(request.svc_pkg_id)
            self.reset_openapi()
            response = self.get_all_routes()
            return response

        @self.router.post("/service-package/del", response_model=List[ResModelOfAPIRoutes])
        async def delete_service_package(request: ReqModelOfDeleteServicePackage, db_conn: Connection = Depends(get_db_conn)):
            launcher_service = ServiceLauncher(self.app, self._logger, db_conn)
            launcher_service.delete_service_package(request.svc_pkg_id)
            self.reset_openapi()
            response = self.get_all_routes()
            return response

    async def load_init_service(self):
        with database.db_conn_static() as db_conn:
            try:
                launcher_service = ServiceLauncher(self.app, self._logger, db_conn)
                launcher_service.load_service_package(None)
                dynamic_routes_response = self.get_all_routes()
                db_conn.commit()
            except Exception as e:
                raise e
        return dynamic_routes_response
