#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.logger import Logger
from api.launcher.api_launcher import ApiLauncher
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from utility.swagger import SwaggerRouter
import multiprocessing
import uvicorn


class CSPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = "default-src *; img-src *; script-src * 'unsafe-inline'; style-src * 'unsafe-inline';"
        return response

logger = Logger()
logger.setLevel("DEBUG")

app = FastAPI(docs_url=None, redoc_url=None, title="Workflow Engine")

api_service_launcher = ApiLauncher(app, logger)
swagger_router = SwaggerRouter(app)

app.include_router(api_service_launcher.get_router(), prefix="/admin")
app.include_router(swagger_router.get_router(), include_in_schema=False)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CSPMiddleware)

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 리소스 정리"""
    try:
        multiprocessing.resource_tracker._resource_tracker._fd = None
    except Exception:
        pass

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return {"detail": "Internal Server Error"}
