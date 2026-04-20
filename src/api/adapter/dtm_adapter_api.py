#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.util_logger import Logger
import api.adapter.schema.engine_adaptor_schema as schema
from api.adapter.schema.engine_adaptor_header import get_file_headers, get_status_headers, FileHeaderModel, StatusHeaderModel
from api.adapter.service.remote_cached_adapter_service import RemoteCachedAdapterService
from api.adapter.service.engine_adaptor_service import EngineAdaptorService
from api.adapter.service.dtm_prediction_service import DtmPredictionService
from api.adapter.service.job_status_service import JobStatusService
from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi import HTTPException, Request
from abc import abstractmethod
import json


class BaseRouter:
    def __init__(self, tags=[]):
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

    def __init__(self, logger=None):
        super().__init__(tags=['DTM Adaptor'])
        # logger = Logger("ADAPTER")
        self._logger = logger
        self._engine_adaptor_service = EngineAdaptorService(logger)
        self._remote_adapter_service = RemoteCachedAdapterService(logger)
        self._job_status_service = JobStatusService(logger, self._remote_adapter_service)
        self._prediction_service = DtmPredictionService(logger, self._remote_adapter_service)
        self._timeout = 3600

    def _cvt_to_json(self, data):
        try:
            clean_data = data.strip().rstrip(",").replace(",}", "}").replace(",]", "]")
            parsed_data = json.loads(clean_data)
            return parsed_data
        except json.JSONDecodeError as e:
            if not isinstance(data, dict):
                self._logger.warn(f"data")
            self._logger.warn(f"Invalid JSON in data field: {str(e)}")
            return data

    def _cvt_params(self, request, body={}):
        params = {}
        if request and request.headers:
            params.update(dict(request.headers))
        if body:
            params.update(dict(body))
        self._logger.debug("Input Params")
        for k, v in params.items():
            self._logger.debug(f" - {k}: {v}")
        return params

    def setup_routes(self):
        @self.router.post(path='/predict/async/web', response_model=schema.ResAdaptWorkflow)
        async def predict_file(request: Request
                               , headers: FileHeaderModel = Depends(get_file_headers)
                               , data: str = Form(...)
                               , file: list[UploadFile] = File(...)
                               , bg: BackgroundTasks = None
                               ):
            self._logger.info("################################################################")
            self._logger.info("#                 < Adapter: Call Prediction >                 #")
            self._logger.info("################################################################")
            job_id = None

            try:
                client_host = request.client.host
                job_id = headers.x_sampl_job_id
                self._logger.info(f" - request client ip: {client_host}")
                self._logger.info(f" - HEADER: {headers}")
                response = await self._prediction_service.run_dtm_prediction(request, headers, data, file, bg)
            except Exception as e:
                self._logger.error(e)
                self._remote_adapter_service.set_job_state(job_id, state='ERROR', error_msg=str(e))
                response = {
                    "data": {},
                    "status": -1,
                    "statusText": "failed"
                }
            return response

        @self.router.post(path='/isworking', response_model=schema.ResAdaptWorkflow)
        async def check_is_working(request: Request):
            self._logger.info("################################################################")
            self._logger.info("#                   < Adapter: Is Working >                    #")
            self._logger.info("################################################################")
            self._logger.info(f" - request client ip: {request.client.host}")

            response = await self._job_status_service.get_is_working()

            self._logger.info(f" - response: {response}")
            return response

        @self.router.post(path='/joblist', response_model=schema.ResAdaptWorkflow)
        async def get_job_list(request: Request, headers: StatusHeaderModel = Depends(get_status_headers)):
            self._logger.info("################################################################")
            self._logger.info("#                   < Adapter: Job List >                      #")
            self._logger.info("################################################################")
            self._logger.info(f" - request client ip: {request.client.host}")
            job_id = headers.x_sampl_job_id
            self._logger.info(f" - job_id: {job_id}")

            response = await self._job_status_service.get_job_list(job_id)

            self._logger.info(f" - response: {response}")
            return response

        @self.router.post(path='/rerun')
        async def get_job_list(request: Request, bg: BackgroundTasks = None):
            self._logger.warn("################################################################")
            self._logger.warn("#                    < Adapter: Re-Run >                       #")
            self._logger.warn("# WARNNING: It use this only test!!                            #")
            self._logger.warn("################################################################")
            self._logger.warn(f" - request client ip: {request.client.host}")
            params = self._cvt_params(request)
            job_id = params.get('job-id')
            callbackable = params.get('x-callbackable', "false")
            if not job_id:
                response = {"result": None, "state": "faile", " message": "not exist job_id"}
            else:
                job_info = self._remote_adapter_service.get_job_info(job_id)
                response = await self._prediction_service.rerun_dtm_prediction(job_id, callbackable, job_info, bg)
            return response
