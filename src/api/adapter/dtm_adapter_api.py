#!/usr/bin/env python
# -*- coding: utf-8 -*-

import api.adapter.schema.engine_adaptor_schema as schema
from api.adapter.schema.engine_adaptor_header import get_file_headers, get_status_headers, FileHeaderModel, StatusHeaderModel
from api.adapter.service.engine_adaptor_service import EngineAdaptorService
from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, FastAPI
from fastapi import HTTPException
from abc import abstractmethod
from typing import Dict
import asyncio
import httpx
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


class EngineAdapter(BaseRouter):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, logger):
        super().__init__(logger, tags=['DTM Adaptor'])
        self._logger = logger
        self._engine_adaptor_service = EngineAdaptorService(logger)

        self._isWorking = False
        self._call_back_error_url = 'http://10.0.0.1:8080/call_back_error'
        self._call_back_url = 'http://10.0.0.1:8080/call_back'
        self._member_id = ''
        self._user_data = ''

    async def _call_workflow_api(self, method: str, path: str, headers: Dict = None, json_data: Dict = None, params: Dict = None):
        """WorkflowEngine API를 내부적으로 호출하는 헬퍼 메서드"""
        self.base_url = 'http://127.0.0.1:8080'
        url = f"{self.base_url}{path}"

        async with httpx.AsyncClient() as client:
            try:
                if method.upper() == "POST":
                    response = await client.post(url, json=json_data, headers=headers, timeout=None)
                elif method.upper() == "GET":
                    response = await client.get(url, params=params, headers=headers, timeout=None)
                elif method.upper() == "PUT":
                    response = await client.put(url, json=json_data, headers=headers, timeout=None)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers, timeout=None)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                if response.status_code >= 400:
                    error_detail = response.json() if response.headers.get('content-type') == 'application/json' else response.text
                    self._logger.error(f"Workflow API error: {error_detail}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=error_detail
                    )

                return response.json()

            except httpx.RequestError as e:
                self._logger.error(f"Request error calling workflow API: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Internal API call failed: {str(e)}"
                )

    def setup_routes(self):
        @self.router.post(path='/predict/web', response_model=schema.ResAdaptWorkflow)
        async def predict_file(headers: FileHeaderModel = Depends(get_file_headers)
                               , data: str = Form(...)
                               , files: list[UploadFile] = File(...)
                               , bg: BackgroundTasks = None):
            self._logger.info("################################################################")
            self._logger.info("#                         < Predict >                          #")
            self._logger.info("################################################################")

            path_list = await self._engine_adaptor_service.upload_files(files)
            job_id = headers.x_sampl_job_id
            call_back_url = headers.x_sampl_callback
            call_back_error_url = headers.x_sampl_err_callback
            member_id = headers.x_sampl_member_id
            user_data = headers.x_sampl_user_data

            self._logger.debug(f" - job_id: {job_id}")
            self._logger.debug(f" - call_back_url: {call_back_url}")
            self._logger.debug(f" - call_back_error_url: {call_back_error_url}")
            self._logger.debug(f" - member_id: {member_id}")
            self._logger.debug(f" - user_data: {user_data}")
            self._logger.debug(f" - file_path: {path_list}")

            asyncio.create_task(self._call_workflow_api
                    (
                    method="POST",
                    path="/api/v1/workflow/inference",
                    headers={
                        "Content-Type": "application/json",
                        "secret_key": "",
                        "job_id": f"{job_id}",
                        "user_id": "test_user",
                        "request-id": str(uuid.uuid4()),
                        "session-id": str(uuid.uuid4()),
                        "call_back_error_url": call_back_url,
                        "call_back_url": call_back_error_url
                    },
                    json_data={"tar_path": path_list}
                )
            )

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

            # bg.add_task(self.call_back_response, req, self._call_back_url, self._user_data)
            return response

        @self.router.post(path='/isworking', response_model=schema.ResAdaptWorkflow)
        async def check_is_working():
            self._logger.info("################################################################")
            self._logger.info("#                       < Is Working >                         #")
            self._logger.info("################################################################")
            result = await asyncio.create_task(self._call_workflow_api(
                    method="GET",
                    path="/api/v1/workflow/working_state",
                    headers={
                        "Content-Type": "application/json"
                    }
                )
            )

            if not result:
                is_working = False
            else:
                is_working = result.get('is_working')


            response = {
                "data": {
                    "isworking": is_working,
                    "async_queue_count": 0,
                    "job_list": []
                },
                "status": 0,
                "statusText": "success"
            }

            return response

        @self.router.post(path='/joblist', response_model=schema.ResAdaptWorkflow)
        async def get_job_list(headers: StatusHeaderModel = Depends(get_status_headers)):
            self._logger.info("################################################################")
            self._logger.info("#                        < Job List >                          #")
            self._logger.info("################################################################")
            job_id = headers.x_sampl_job_id
            result = await asyncio.create_task(self._call_workflow_api(
                    method="GET",
                    path="/api/v1/workflow/job_state",
                    headers={
                        "Content-Type": "application/json",
                        "secret_key": "",
                        "job_id": f"{job_id}",
                    }
                )
            )
            if not result:
                completion_yn = 'N'
                start_datetime = "0"
                end_datetime = "0"
                status = None
                call_back_url = None
                call_back_error_url = None
                error_yn = 'N'
            else:
                processing_time = result.get('processing_time')
                start_datetime = processing_time.get('start_dt', "0")
                end_datetime = processing_time.get('end_dt', "0")
                status = result.get('status')
                params = result.get('params', {})
                if params:
                    call_back_url = params.get('call_back_url')
                    call_back_error_url = params.get('call_back_error_url')
                else:
                    call_back_url = None
                    call_back_error_url = None

                if status == 'COMPLETED':
                    completion_yn = 'Y'
                    error_yn = "N"
                elif status == 'FAILED':
                    completion_yn = 'Y'
                    error_yn = "Y"
                else:
                    completion_yn = 'N'
                    error_yn = 'N'

            response = {
                "data": {
                    "cnt": 0,
                    "data": [{
                        "call_back_error_url": call_back_error_url,
                        "call_back_url": call_back_url,
                        "completion_yn": completion_yn,
                        "conveyor": "ocr_online",
                        "data": {},
                        "end_datetime": end_datetime,
                        "error_yn": error_yn,
                        "job_id": job_id,
                        "member_id": self._member_id,
                        "message": "Success",
                        "notified": "",
                        "pid": 0,
                        "pid_created_time": 0,
                        "reg_datetime": start_datetime,
                        "start_datetime": start_datetime,
                        "status": status,
                        "thread_id": 0,
                        "uid": ""
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
