#!/usr/bin/env python
# -*- code utf-8 -*-

from typing import Annotated

from ailand.common.database import db_conn as get_db_conn
from ailand.router.airouter import BaseRouter
from fastapi import Depends
from pymysql import Connection

import api.helloworld.schema.helloworld_schema as schema
from api.helloworld.service.helloworld_service import HelloWorldService
from api.schema.schema import BaseResponse


class HelloWorldRouter(BaseRouter):
    def __init__(self):
        super().__init__(tags=["HelloWorld"])

    def setup_routes(self):
        @self.router.post('/greet', response_model=BaseResponse[schema.ResModelOfGreet])
        async def greet(req: schema.ReqModelOfGreet, db_conn: Annotated[Connection, Depends(get_db_conn)]):
            helloworld_service = HelloWorldService(self._logger, db_conn)
            greeting = helloworld_service.greet(req.model_dump())
            result = {
                'result': {
                    'greeting': greeting
                }
            }
            return result
