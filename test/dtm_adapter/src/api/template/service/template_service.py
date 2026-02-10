#!/usr/bin/env python
# -*- coding: utf-8 -*-


import httpx
import asyncio

from api.workflow.protocol.schema import BaseResponse
from api.workflow.protocol.workflow_headers import HeaderModel, get_headers, get_dtm_headers, DtmHeaderModel
from api.dtm.service.file_service import FileService
from fastapi import APIRouter, WebSocket, Depends, UploadFile, File, Form, BackgroundTasks
from multiprocessing import Queue
from abc import abstractmethod
from typing import Any
import api.dtm.protocol.dtm_schema as schema
import uuid


class BaseRouter:
    def __init__(self, logger=None, tags=[]):
        self._logger = logger
        self.router = APIRouter(tags=tags)
        self.setup_routes()

    @abstractmethod
    def setup_routes(self):
        pass

    def get_router(self) -> APIRouter:
        return self.router


class WorkflowAdaptor(BaseRouter):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, logger, db_conn=None):
        super().__init__(logger, tags=['Workflow Engine'])
        self._job_Q = Queue()
        self._files_service = FileService(logger)

    def setup_routes(self):
        @self.router.post(path='/predict/web', response_model=BaseResponse[schema.ResAdaptWorkflow])
        async def adapt_workflow(headers: DtmHeaderModel = Depends(get_dtm_headers),
                                 data: str = Form(...),
                                 files: list[UploadFile] = File(...), bg: BackgroundTasks = None):
            self._logger.info("################################################################")
            self._logger.info("#                         < FileUpload >                         #")
            self._logger.info("################################################################")
            path_list = await self._files_service.upload_files(files)
            job_id = headers.x_sampl_job_id
            self._redis_access.hset(key=job_id, mapping={'custom_params': 'test_params'})

            response = {
                'result': {
                    "data": {},
                    "status": 0,
                    "statusText": "success"
                }
            }
            req = {
                "from_node": "Input_zla_r0_node.query_input",
                "to_node": "Output_OvdARr_node.output",
                "parameter": {
                    "request_id": job_id,
                    "query": "에이전트의 기본 구성 요소는?",
                    "file_paths": path_list,
                    "file_urls": []
                }
            }


            bg.add_task(self.workflow_run, req)
            return response

    async def workflow_run(self, req):
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post("http://10.147.126.50:8080/api/v1/workflow/run", json=req, headers={
                'request-id': '1234',
                'session-id': 'asd1234',
                'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxOTU1RjdGM0NGOSIsImlhdCI6MTc0MTEzMDY0OCwidXNyX2lkIjoiMTk1NUY3RjNDRjkiLCJlbXBuIjoiNzk3ODciLCJlbWFpbCI6InJvb3RUZXN0QGhhbmFmbi5jb20iLCJjbXB5X2NkIjoiRFQiLCJleHAiOjE3NDM3NTUwNDh9.fm_lIm6vroZXK4QXtpmVuIcDhkOOo34Sky_vyXDfb1M',
                'Content-Type': 'application/json'
            })
