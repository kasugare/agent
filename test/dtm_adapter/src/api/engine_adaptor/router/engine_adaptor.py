#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

import httpx
import asyncio

import api.adapter.schema.engine_adaptor_schema as schema
from api.adapter.schema.engine_adaptor_header import get_file_headers, get_status_headers, FileHeaderModel, \
    StatusHeaderModel
from api.adapter.service.engine_adaptor_service import EngineAdaptorService
from fastapi import APIRouter, WebSocket, Depends, UploadFile, File, Form, BackgroundTasks, FastAPI
from multiprocessing import Queue
from abc import abstractmethod


class BaseRouter:
    def __init__(self, app: FastAPI, logger=None, tags=[]):
        self.app = app
        self._logger = logger
        self.router = APIRouter(tags=tags)
        self.setup_routes()

    @abstractmethod
    def setup_routes(self):
        pass

    def get_router(self) -> APIRouter:
        return self.router


class EngineAdapter(BaseRouter):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, app: FastAPI, logger):
        super().__init__(app, logger, tags=['Engine Adaptor'])
        self._job_Q = Queue()
        self._engine_adaptor_service = EngineAdaptorService(logger)

        self._isWorking = False
        self._call_back_error_url = ''
        self._call_back_url = ''
        self._member_id = ''
        self._user_data = ''

    def setup_routes(self):
        @self.router.post(path='/predict/web', response_model=schema.ResAdaptWorkflow)
        async def predict_file(headers: FileHeaderModel = Depends(get_file_headers),
                               data: str = Form(...),
                               files: list[UploadFile] = File(...), bg: BackgroundTasks = None):
            path_list = await self._engine_adaptor_service.upload_files(files)
            job_id = headers.x_sampl_job_id
            self.user_data = headers.x_sampl_user_data
            self._call_back_url = headers.x_sampl_callback
            self._call_back_error_url = headers.x_sampl_err_callback
            self._member_id = headers.x_sampl_member_id
            self.user_data = headers.x_sampl_user_data

            self._logger.info(f"x_sampl_user_data : {self.user_data}")
            self._logger.info(f"callback_url : {self._call_back_url}")

            response = {
                "data": {},
                "status": 0,
                "statusText": "success"
            }
            req = {
                "status": 0,
                "statusText": "success",
                "data": {
                    "project": "ocr",
                    "blueprint": "detection",
                    "tags": {},
                    "result": {
                        "uuid": "abc",
                        "image": [
                            {
                                "uuid": 1,
                                "name": "test.png",
                                "success": "Y",
                                "page": 1,
                                "data": [],
                                "documentClassification": [],
                                "textExtraction": [],
                                "extData": {
                                    "extract": []
                                },
                                "error": {
                                    "code": 0,
                                    "msg": ""
                                }
                            }
                        ]
                    },
                    "data": {
                        "user_id": "admin",
                        "user_uid": 1,
                        "site_uid": 1,
                        "infer_uid": 1,
                        "batch_uid": "25a97d7e11504b83bf1cebe909e075bf",
                        "uuid": "25a97d7e11504b83bf1cebe909e075bf"
                    }
                }
            }

            bg.add_task(self.call_back_response, req, self._call_back_url, self._user_data)
            return response

        @self.router.post(path='/isworking', response_model=schema.ResAdaptWorkflow)
        async def check_is_working():
            response = {
                "data": {
                    "isworking": self._isWorking,
                    "async_queue_count": 0,
                    "job_list": []
                },
                "status": 0,
                "statusText": "success"
            }

            return response

        @self.router.post(path='/joblist', response_model=schema.ResAdaptWorkflow)
        async def get_job_list(headers: StatusHeaderModel = Depends(get_status_headers)):
            job_id = headers.x_sampl_job_id
            response = {
                "data": {
                    "cnt": 0,
                    "data": [{
                        "call_back_error_url": self._call_back_error_url,
                        "call_back_url": self._call_back_url,
                        "completion_yn": "Y",
                        "conveyor": "ocr_online",
                        "data": {},
                        "end_datetime": "20251111010842",
                        "error_yn": "N",
                        "job_id": job_id,
                        "member_id": self._member_id,
                        "message": "Success",
                        "notified": "",
                        "pid": 900,
                        "pid_created_time": 1762822473.55,
                        "reg_datetime": "20251111010837",
                        "start_datetime": "20251111010837",
                        "status": "COMPLETED",
                        "thread_id": 140084576745216,
                        "uid": "900-1762822473.55-OCR-1.29.31.34290ce846db4019a664f4e2b9c955d6"
                    }]
                },
                "status": 0,
                "statusText": "success"
            }

            return response

    async def call_back_response(self, req, url, user_data):
        self._isWorking = True
        print('sleep start')
        await asyncio.sleep(60)
        print('sleep end')
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=req, headers={
                'X-SAMPL-USER-DATA': user_data,
                'Content-Type': 'application/json'
            })
            self._logger.info(response)
            self._isWorking = False
