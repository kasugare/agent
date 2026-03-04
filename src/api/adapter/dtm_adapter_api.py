#!/usr/bin/env python
# -*- coding: utf-8 -*-

import api.adapter.schema.engine_adaptor_schema as schema
from api.adapter.schema.engine_adaptor_header import get_file_headers, get_status_headers, FileHeaderModel, StatusHeaderModel
from api.adapter.service.engine_adaptor_service import EngineAdaptorService
from api.adapter.service.callback_result import CallbackApiRequester
from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from abc import abstractmethod
from typing import Dict
import asyncio
import httpx
import json


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
        self._callback_requester = CallbackApiRequester(logger)

        self._isWorking = False
        self._member_id = ''
        self._user_data = ''

    async def _call_workflow_api(self, base_url: str, method: str, path: str, headers: Dict = None, json_data: Dict = None, params: Dict = None):
        if not base_url:
            raise HTTPException(
                status_code=500,
                detail=f"Internal API call failed: - check base_url: {base_url}"
            )
        if base_url[-1] == "/":
            url_path = f"{base_url[:-1]}{path}"
        else:
            url_path = f"{base_url}{path}"

        async with httpx.AsyncClient() as client:
            try:
                if method.upper() == "POST":
                    response = await client.post(url_path, json=json_data, headers=headers, timeout=None)
                elif method.upper() == "GET":
                    response = await client.get(url_path, params=params, headers=headers, timeout=None)
                elif method.upper() == "PUT":
                    response = await client.put(url_path, json=json_data, headers=headers, timeout=None)
                elif method.upper() == "DELETE":
                    response = await client.delete(url_path, headers=headers, timeout=None)
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

    async def call_back_response(self, base_url, route_path, call_method, req_headers, json_data, callback_header, callback_data_info):
        def read_file(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as fd:
                    json_data = json.load(fd)
            except FileNotFoundError:
                self._logger.warn("File not found error")
                raise FileNotFoundError
            except json.JSONDecodeError:
                self._logger.warn("json decoding error")
                raise json.JSONDecodeError
            except Exception as e:
                self._logger.error(e)
                raise Exception
            return json_data

        status_code = -1
        result_data = []
        result = {}
        job_id = req_headers.get('job_id', "EMPTY_JOB_ID")
        try:
            self._logger.info(f"call prediction on engine: {job_id}")
            result = await asyncio.create_task(
                self._call_workflow_api(
                    base_url=base_url,
                    method=call_method,
                    path=route_path,
                    headers=req_headers,
                    json_data=json_data
                )
            )

            self._logger.debug(f"[{job_id}] Job completed, result: {result}")
            result_message = result.get('result', {})
            if isinstance(result_message, dict):
                result_state = result_message.get('status')
                if result_state in ['success']:
                    result_file_path = result_message.get('result')
                    status_code = 0
                    status_text = result_state
                    result_data = read_file(result_file_path)
                else:
                    error_message = result_message.get('error')
                    status_code = -1
                    status_text = error_message
            else:
                status_text = 'ValidError: result format is not valid'
        except FileNotFoundError as e:
            self._logger.warn(f"[{job_id}]: file not found error, result: {result}")
            status_code = -1
            status_text = f"{type(e).__name__}: {e}"
        except Exception as e:
            self._logger.warn(f"[{job_id}]: Unknown Error, result: {result}")
            status_code = -1
            status_text = f"{type(e).__name__}: {e}"
        result_pack = {
            'status_code': status_code,
            'status_text': status_text,
            'result_data': result_data
        }
        self._callback_requester.call_back_result(callback_header, callback_data_info, result_pack)

    def _cvt_to_json(self, data):
        try:
            clean_data = data.strip().rstrip(",").replace(",}", "}").replace(",]", "]")
            parsed_data = json.loads(clean_data)
            return parsed_data
        except json.JSONDecodeError as e:
            return JSONResponse(status_code=400, content={"error": f"Invalid JSON in data field: {str(e)}"})

    def setup_routes(self):
        @self.router.post(path='/predict/async/web', response_model=schema.ResAdaptWorkflow)
        async def predict_file(request: Request
                               , headers: FileHeaderModel = Depends(get_file_headers)
                               , data: str = Form(...)
                               , file: list[UploadFile] = File(...)
                               , bg: BackgroundTasks = None):
            self._logger.info("################################################################")
            self._logger.info("#                 < Adapter: Call Prediction >                 #")
            self._logger.info("################################################################")

            try:
                self._logger.info(f"request client ip: {request.client.host}")
                self._logger.info(headers)

                job_id = headers.x_sampl_job_id
                call_back_url = headers.x_sampl_callback
                call_back_error_url = headers.x_sampl_err_callback
                member_id = headers.x_sampl_member_id
                user_callback_data = headers.x_sampl_user_data

                data_body = self._cvt_to_json(data)
                tags = data_body.get('tags', {})
                data_info = data_body.get('data', {})
                tar_path_list = await self._engine_adaptor_service.upload_files(file)

                self._logger.debug(f" - [{job_id}] engine_url   : {request.base_url}")
                self._logger.debug(f" - [{job_id}] client ip    : {request.client.host}")
                self._logger.debug(f" - [{job_id}] call_back_url      : {call_back_url}")
                self._logger.debug(f" - [{job_id}] call_back_error_url: {call_back_error_url}")
                self._logger.debug(f" - [{job_id}] member_id    : {member_id}")
                self._logger.debug(f" - [{job_id}] user_data    : {user_callback_data}")
                self._logger.debug(f" - [{job_id}] tar_path_list: {tar_path_list}")
                self._logger.debug(f" - [{job_id}] tags         : {tags}")
                self._logger.debug(f" - [{job_id}] data_info    : {data_info}")

                base_url = str(request.base_url)
                route_path = "/api/v1/workflow/inference"
                call_method = "POST"
                req_headers = {
                    "Content-Type": "application/json",
                    "secret_key": "",
                    "job_id": f"{job_id}",
                    "user_id": f"{member_id}",
                    "user_callback_data": f"{user_callback_data}",
                    "file_path_list": json.dumps(tar_path_list),
                    "request-id": str(job_id),
                    "session-id": str(job_id),
                    "call_back_error_url": call_back_error_url,
                    "call_back_url": call_back_url
                }
                json_data = {"tar_path": tar_path_list}
                bg.add_task(self.call_back_response, base_url, route_path, call_method, req_headers, json_data, headers, data_body)
            except Exception as e:
                self._logger.error(e)
            response = {
                "data": {},
                "status": 0,
                "statusText": "success"
            }
            return response

        @self.router.post(path='/isworking', response_model=schema.ResAdaptWorkflow)
        async def check_is_working(request: Request):
            self._logger.info("################################################################")
            self._logger.info("#                   < Adapter: Is Working >                    #")
            self._logger.info("################################################################")
            self._logger.info(f"request client ip: {request.client.host}")
            result = {}
            try:
                result = await asyncio.create_task(self._call_workflow_api(
                        base_url=str(request.base_url),
                        method="GET",
                        path="/api/v1/workflow/working_state",
                        headers={
                            "Content-Type": "application/json"
                        }
                    )
                )
            except Exception as e:
                self._logger.error(e)

            response = {
                "data": {
                    "isworking": result.get('is_working', False),
                    "async_queue_count": 0,
                    "job_list": []
                },
                "status": result.get('state'),
                "statusText": result.get('message')
            }

            return response

        @self.router.post(path='/joblist', response_model=schema.ResAdaptWorkflow)
        async def get_job_list(request: Request, headers: StatusHeaderModel = Depends(get_status_headers)):
            self._logger.info("################################################################")
            self._logger.info("#                   < Adapter: Job List >                      #")
            self._logger.info("################################################################")
            self._logger.info(f"request client ip: {request.client.host}")
            job_id = headers.x_sampl_job_id
            self._logger.info(f" - job_id: {job_id}")
            result = None
            try:
                result = await asyncio.create_task(self._call_workflow_api(
                        base_url=str(request.base_url),
                        method="GET",
                        path="/api/v1/workflow/job_state",
                        headers={
                            "Content-Type": "application/json",
                            "secret_key": "",
                            "job_id": f"{job_id}",
                        }
                    )
                )
            except Exception as e:
                self._logger.error(e)

            if not result:
                completion_yn = 'N'
                reg_datetime = "0"
                start_datetime = "0"
                end_datetime = "0"
                status = None
                call_back_url = None
                call_back_error_url = None
                error_yn = 'N'
            else:
                processing_time = result.get('processing_time')
                reg_datetime = processing_time.get('assigned_dt', "0")
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
                        "reg_datetime": reg_datetime,
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
