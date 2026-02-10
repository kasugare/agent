#!/usr/bin/env python
# -*- code utf-8 -*-

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.engine_adaptor.router.engine_adaptor import EngineAdaptor
from error.exception_handler import register_exception_handlers
from utility.middleware import CSPMiddleware
from utility.swagger import SwaggerRouter
from common.logger import Logger
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(docs_url=None, redoc_url=None, title="Engine Adaptor")

logger = Logger()
logger.setLevel("DEBUG")

# create init classes
api_engine_adaptor = EngineAdaptor(app, logger)
swagger_router = SwaggerRouter(app)

# add base routers
app.include_router(api_engine_adaptor.get_router(), prefix="/api/v1")
app.include_router(swagger_router.get_router(), include_in_schema=False)

# add base exception handlers
register_exception_handlers(app)

# add base middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CSPMiddleware)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
