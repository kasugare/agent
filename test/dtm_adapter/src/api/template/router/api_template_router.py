#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import List

from ailand.common import database
from ailand.common.database import db_conn as get_db_conn
from ailand.router.airouter import BaseRouter
from fastapi import FastAPI, Depends
from fastapi.routing import APIRoute
from pymysql import Connection

import api.template.schema.template_schema as schema
from api.template.service.template_service import ServiceTemplate
from api.schema.schema import BaseResponse

class ApiTemplate(BaseRouter):

    def __init__(self, app: FastAPI):
        super().__init__(tags=["TEMPLATE"])
        self.app = app

    def get_app(self):
        return self.app

    def reset_openapi(self):
        self.app.openapi_schema = None
        self.app.openapi()

    def parse_route(self, route: APIRoute) -> schema.ResModelOfAPIRoutes:
        response = schema.ResModelOfAPIRoutes(
            path=route.path,
            name=route.name,
            methods=list(route.methods),
            function=route.endpoint.__name__
        )
        return response

    def get_all_routes(self) -> List[schema.ResModelOfAPIRoutes]:
        routes = []
        for route in self.app.routes:
            if isinstance(route, APIRoute):
                routes.append(self.parse_route(route))
        return routes

    def setup_routes(self):
        @self.router.post("/template/get", response_model=BaseResponse[schema.ResModelOfGetTemplatePool])
        async def get_template(request: schema.ReqModelOfGetTemplatePool,
                               db_conn: Connection = Depends(get_db_conn)):
            template_service = ServiceTemplate(self.app, self._logger, db_conn)
            self._logger.debug("/template/get api Start")
            tpl_id = request.tpl_id
            self._logger.debug(f"Request Template Id : {tpl_id}")
            result = template_service.get_template(tpl_id)

            response = {
                'result': result
            }
            return response

        @self.router.post("/templates/get", response_model=BaseResponse[schema.ResModelOfGetTemplatesPool])
        async def get_templates(request: schema.ReqModelOfGetTemplatesPool,
                               db_conn: Connection = Depends(get_db_conn)):
            template_service = ServiceTemplate(self.app, self._logger, db_conn)
            self._logger.debug("/templates/get api Start")
            result = template_service.get_templates()
            response = {
                'result': {
                    'templates': result
                }
            }
            return response

        @self.router.post("/template/delete", response_model=BaseResponse[schema.ResModelOfDeleteTemplatePool])
        async def delete_template(request: schema.ReqModelOfDeleteTemplatePool,
                                  db_conn: Connection = Depends(get_db_conn)):
            template_service = ServiceTemplate(self.app, self._logger, db_conn)
            tpl_id = request.tpl_id
            usr_id = request.usr_id
            self._logger.debug("/template/delete api Start")
            self._logger.debug(f"Request Template Id : {tpl_id}")
            self._logger.debug(f"Request User Id : {usr_id}")
            template_service.delete_template(tpl_id, usr_id)
            result = {"tpl_id": tpl_id}
            response = {
                'result': result
            }
            return response

        @self.router.post("/template/create", response_model=BaseResponse[schema.ResModelOfCreateTemplatePool])
        async def create_template(request: schema.ReqModelOfCreateTemplatePool,
                                  db_conn: Connection = Depends(get_db_conn)):
            template_service = ServiceTemplate(self.app, self._logger, db_conn)
            self._logger.debug("/template/create api Start")
            self._logger.debug("Request Template Id : ", request.model_dump())
            dply_typ_cd= request.dply_typ_cd
            tpl_typ_cd = request.tpl_typ_cd
            params = request.params
            mnfst = request.mnfst
            usr_id = request.usr_id
            tpl_id = template_service.create_template(dply_typ_cd=dply_typ_cd, tpl_typ_cd=tpl_typ_cd, params=params, mnfst=mnfst, usr_id=usr_id)
            result = {"tpl_id": tpl_id}
            response = {
                "result": result
            }
            return response

        @self.router.post("/dpl-typ-cd/get", response_model=BaseResponse[schema.ResModelOfGetDeployTypeCode])
        async def get_deploy_type_code(request: schema.ReqModelOfGetDeployTypeCode,
                                       db_conn: Connection = Depends(get_db_conn)):
            template_service = ServiceTemplate(self.app, self._logger, db_conn)
            self._logger.debug("/dpl-typ-cd/get api Start")
            dply_typ_cds = template_service.get_deploy_type_code()
            response = {
                'result': {'dply_typ_cds': dply_typ_cds}
            }
            return response

        @self.router.post("/tpl-typ-cd/get", response_model=BaseResponse[schema.ResModelOfGetTemplateTypeCode])
        async def get_template_type_code(request: schema.ReqModelOfGetTemplateTypeCode,
                                         db_conn: Connection = Depends(get_db_conn)):
            template_service = ServiceTemplate(self.app, self._logger, db_conn)
            self._logger.debug("/tpl-typ-cd/get api Start")
            tpl_typ_cds = template_service.get_template_type_code()
            response = {
                'result': {'tpl_typ_cds': tpl_typ_cds}
            }
            return response


    async def load_init_service(self):
        with database.db_conn_static() as db_conn:
            try:
                template_service = ServiceTemplate(self.app, self._logger, db_conn)
                template_service.load_service_package(None)
                dynamic_routes_response = self.get_all_routes()
                db_conn.commit()
            except Exception as e:
                raise e
        return dynamic_routes_response
