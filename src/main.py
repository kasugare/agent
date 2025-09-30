#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.logger import Logger
from api.launcher.api_launcher import ApiLauncher
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import multiprocessing
import uvicorn
from common.dependancy import create_redis_client
from common.create_module import CreateModule

# create_module = CreateModule()
# create_module.create_all_packages('/data/kelly/pycharm_projects/agent/src/app/_simple_rag')
# create_module.register_zip_packages('/data/kelly/pycharm_projects/agent/src/app/_simple_rag')

class CSPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = "default-src *; img-src *; script-src * 'unsafe-inline'; style-src * 'unsafe-inline';"
        return response

# class AppWorkflowEngine:
# 	def __init__(self):
# 		self._logger = Logger().getLogger()
# 		self._logger.error_pool("### Start App Workflow Serving Engine ###")
#
# 	def do_process(self):
# 		app = FastAPI()
# 		api_service_launcher = ApiLauncher(app, self._logger)
# 		app.include_router(api_service_launcher.get_router(), prefix="/admin")

# def run():
# 	wfEngine = AppWorkflowEngine()
# 	wfEngine.do_process()


logger = Logger()
logger.setLevel("DEBUG")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CSPMiddleware)
api_service_launcher = ApiLauncher(app, logger)
app.include_router(api_service_launcher.get_router(), prefix="/admin")

# @app.on_event("startup")
# async def startup_event():
#     app.state.redis_clients = {
#         "meta": create_redis_client(redis_databases=1),
#         "data": create_redis_client(redis_databases=2),
#         "task": create_redis_client(redis_databases=3),
#     }


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



# @app.on_event("startup")
# async def startup_event():
#     sentinel_hosts = "ailand.ai:30379"
#     master_name = "mymaster"
#     password = "mypassword"
#
#     create_redis_client(app, sentinel_hosts, master_name, password)
# @app.on_event("shutdown")
# async def shutdown_event():
#     if hasattr(app.state, "redis_client"):
#         app.state.redis_client.close()




if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=18000,
        workers=3,
        timeout_keep_alive=0  # Keep-Alive 비활성화
    )