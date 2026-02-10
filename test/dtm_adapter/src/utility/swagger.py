# -*- coding: utf-8 -*-
# !/usr/bin/env python
from pathlib import Path

from ailand.router.airouter import BaseRouter
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html, get_redoc_html
from starlette.staticfiles import StaticFiles


class SwaggerRouter(BaseRouter):
    def __init__(self, app: FastAPI):
        super().__init__(tags=['SWAGGER'])
        self.app = app
        self.app.mount("/static", StaticFiles(directory=Path(__file__).parent.parent / "static"), name="static")
        self.setup_routes()

    def setup_routes(self):
        @self.router.get("/docs")
        async def custom_swagger_ui_html():
            return get_swagger_ui_html(
                openapi_url=self.app.openapi_url,
                title=self.app.title + " - Swagger UI",
                oauth2_redirect_url=self.app.swagger_ui_oauth2_redirect_url,
                swagger_js_url="/static/swagger-ui-bundle.js",
                swagger_css_url="/static/swagger-ui.css",
            )

        @self.router.get("/api/v1/openapi.json", include_in_schema=False)
        async def swagger_ui_redirect():
            return get_swagger_ui_oauth2_redirect_html()

        @self.router.get("/redoc", include_in_schema=False)
        async def redoc_html():
            return get_redoc_html(
                openapi_url=self.app.openapi_url,
                title=self.app.title + " - ReDoc",
                redoc_js_url="/static/redoc.standalone.js",
                with_google_fonts=False,
            )
