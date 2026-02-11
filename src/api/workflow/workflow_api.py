#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.conf_serving import getWorkflowId
from api.workflow.service.admin.metric_service import MetricService
from api.workflow.service.meta.auto_meta_loader import AutoMetaLoader
from api.workflow.service.meta.wf_meta_parser import WorkflowMetaParser
from api.workflow.service.meta.prompt_meta_generator import PromptMetaGenerator
from api.workflow.service.execute.workflow_executor import WorkflowExecutor
from api.workflow.service.stream.web_stream_connection_manager import WSConnectionManager
from api.workflow.service.meta.meta_store_service import MetaStoreService
from api.workflow.service.data.data_store_service import DataStoreService
from api.workflow.service.task.task_store_service import TaskStoreService
from api.workflow.service.stream.web_stream_handler import WebStreamHandler
from api.workflow.protocol.schema import BaseResponse
from api.workflow.protocol.workflow_headers import HeaderModel, get_headers
from api.workflow.error_pool.error import NotDefinedWorkflowMetaException
from error.parent_exception import InvalidInputException
from error.parent_exception import NotDefinedMetaException
from fastapi import APIRouter, WebSocket, Depends, Request
from abc import abstractmethod
from typing import Any
import api.workflow.protocol.workflow_schema as schema
import uuid
import time


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


class WorkflowEngine(BaseRouter):
    def __init__(self, logger):
        super().__init__(logger, tags=['Workflow Engine'])
        self._ws_manager = WSConnectionManager(logger)
        self._metric_service = MetricService(logger)

        auto_meta_loader = AutoMetaLoader(self._logger)
        auto_meta_loader.init_workflow_meta()

        self._task_pool = {}

    def _set_task_executor(self, job_id, executor):
        if len(self._task_pool) > 10:
            self._task_pool.popitem()
        else:
            self._task_pool[job_id] = executor

    def _get_task_executor(self, job_id) -> WorkflowExecutor:
        task_executor = self._task_pool.get(job_id, {})
        return task_executor

    def _get_executor_all(self):
        return self._task_pool

    def _cvt_params(self, request, body={}):
        params = {}
        if request and request.headers:
            params.update(dict(request.headers))
        if body:
            params.update(dict(body))
        self._logger.debug("Input Params")
        for k, v in params.items():
            self._logger.warn(f" - {k}: {v}")
        return params

    def _set_store_pack(self, wf_id, job_id):
        store_pack = {}
        metastore = MetaStoreService(self._logger, wf_id)
        datastore = DataStoreService(self._logger, job_id)
        taskstore = TaskStoreService(self._logger, job_id)
        store_pack['metastore'] = metastore
        store_pack['datastore'] = datastore
        store_pack['taskstore'] = taskstore
        return store_pack


    def setup_routes(self):
        @self.router.post(path='/workflow/meta', response_model=BaseResponse[schema.ResCreateWorkflow])
        async def create_workflow(headers: HeaderModel = Depends(get_headers), request: schema.ReqCreateWorkflow = ...):
            self._logger.info("################################################################")
            self._logger.info("#                         < Set Meta >                         #")
            self._logger.info("################################################################")
            request_id = headers.request_id
            new_wf_meta = request.meta

            if not request_id:
                request_id = format(int(time.time() * 100000), "X")

            if not new_wf_meta:
                self._logger.warn("InvalidInputException: invalid workflow meta")
                raise InvalidInputException(err_detail="Invalid workflow meta")

            meta_paraser = WorkflowMetaParser(self._logger)
            meta_pack = meta_paraser.parse_wf_meta(new_wf_meta)
            wf_id = meta_pack.get('workflow_id')
            metastore = MetaStoreService(self._logger, wf_id)
            metastore.set_wf_meta(meta_pack, request_id)
            return {}

        @self.router.post(path='/workflow/prompt', response_model=BaseResponse[dict[str, Any]])
        async def call_prompt_test(headers: HeaderModel = Depends(get_headers), request: schema.ReqCreateWorkflow = ...):
            self._logger.info("################################################################")
            self._logger.info("#                      < Prompt Tester >                       #")
            self._logger.info("################################################################")
            request_id = headers.request_id
            params = request.meta
            prompt_meta_generator = PromptMetaGenerator(self._logger)
            wf_meta_template = prompt_meta_generator.gen_prompt_meta_data(params)
            meta_paraser = WorkflowMetaParser(self._logger)
            new_meta_pack = meta_paraser.parse_wf_meta(wf_meta_template)
            wf_id = new_meta_pack.get('workflow_id')

            metastore = MetaStoreService(self._logger, wf_id)
            metastore.set_wf_meta(new_meta_pack, request_id)

            response = {}
            try:
                job_id = params.get('job_id', str(uuid.uuid4()))
                datastore = DataStoreService(self._logger, request_id)
                store_pack = self._set_store_pack(wf_id, job_id)
                workflow_executor = WorkflowExecutor(self._logger, store_pack)
                result = workflow_executor.run_workflow(params)
                response = {
                    "result": result
                }
            except NotDefinedWorkflowMetaException as e:
                raise NotDefinedMetaException(err_detail="Not defined workflow meta")
            except AttributeError as e:
                raise InvalidInputException(err_detail="Not defined node_id(s)")
            except Exception as e:
                self._logger.error(e)
            return response

        @self.router.get(path='/workflow/clear', response_model=BaseResponse[schema.ResCallDataClear])
        async def call_data_clear(headers: HeaderModel = Depends(get_headers), request: schema.ReqCallDataClear = ...):
            self._logger.info("################################################################")
            self._logger.info("#                         < Clear All >                        #")
            self._logger.info("################################################################")
            return {}

        @self.router.post(path='/workflow/run', response_model=BaseResponse[dict[str, Any]])
        async def call_chained_model_service(request: Request, body: dict):
            self._logger.info("################################################################")
            self._logger.info("#                            < RUN >                           #")
            self._logger.info("################################################################")
            params = self._cvt_params(request, body)
            response = {}

            try:
                req_id = params.get('request-id')
                session_id = params.get('session-id', req_id)
                wf_id = params.get('workflow_id', getWorkflowId())
                job_id = params.get('job_id', session_id)
                store_pack = self._set_store_pack(wf_id, job_id)
                workflow_executor = WorkflowExecutor(self._logger, store_pack)
                result = workflow_executor.run_workflow(params)
                response = {
                    "result": result
                }
            except NotDefinedWorkflowMetaException as e:
                raise NotDefinedMetaException(err_detail="Not defined workflow meta")
            except AttributeError as e:
                raise InvalidInputException(err_detail="Not defined node_id(s)")
            except Exception as e:
                self._logger.error(e)
            return response

        @self.router.post(path='/workflow/inference', response_model=BaseResponse[dict[str, Any]])
        async def call_chained_model_service(request: Request, body: dict):
            self._logger.info("################################################################")
            self._logger.info("#                        < INFERENCE >                         #")
            self._logger.info("################################################################")

            params = self._cvt_params(request, body)
            response = {}

            try:
                req_id = params.get('request-id')
                session_id = params.get('session-id', req_id)
                wf_id = params.get('workflow_id', getWorkflowId())
                job_id = params.get('job_id', session_id)
                store_pack = self._set_store_pack(wf_id, job_id)
                workflow_executor = WorkflowExecutor(self._logger, store_pack)
                result = workflow_executor.run_workflow(params)
                self._set_task_executor(job_id, workflow_executor)
                response = {
                    "result": result
                }
            except NotDefinedWorkflowMetaException as e:
                raise NotDefinedMetaException(err_detail="Not defined workflow meta")
            except AttributeError as e:
                raise InvalidInputException(err_detail="Not defined node_id(s)")
            except Exception as e:
                self._logger.error(e)
            return response

        @self.router.get(path='/workflow/metapack')
        async def call_meta_pack(wf_id=None):
            self._logger.warn("################################################################")
            self._logger.warn("#                         < Meta Pack >                        #")
            self._logger.warn("################################################################")
            # meta_pool = self._meta_service_pool.get_service_pool()
            meta_pool = {}
            for wf_id, metastore in meta_pool.items():
                self._logger.debug(f" <{wf_id}>")
                meta_pack = metastore.get_meta_pack_service()
                for k, v in meta_pack.items():
                    self._logger.debug(f" - {k} : \t{v}")
            return meta_pool

        @self.router.get(path='/workflow/datapool')
        async def call_data_pool(request: Request):
            self._logger.info("################################################################")
            self._logger.info("#                         < Data Pool >                        #")
            self._logger.info("################################################################")
            datastore = DataStoreService(self._logger, "test")
            data_pool = self._metric_service.extract_io_data(datastore)
            return data_pool

        @self.router.get(path='/workflow/act_dag')
        async def call_active_dag(request: Request):
            self._logger.info("################################################################")
            self._logger.info("#                        < Active DAG >                        #")
            self._logger.info("################################################################")
            params = self._cvt_params(request)
            job_id = params.get('job-id')
            workflow_executor = self._get_task_executor(job_id)
            if not workflow_executor:
                return

            active_meta = self._metric_service.extract_active_dag(workflow_executor)
            return active_meta

        @self.router.get(path='/workflow/tasks')
        async def call_task_pool(request: Request):
            self._logger.info("################################################################")
            self._logger.info("#                       < Active Tasks >                       #")
            self._logger.info("################################################################")
            params = self._cvt_params(request)
            job_id = params.get('job-id')
            workflow_executor = self._get_task_executor(job_id)
            if not workflow_executor:
                return
            active_tasks = self._metric_service.extract_active_task_pool()
            return active_tasks

        @self.router.get(path='/workflow/job_state')
        async def call_job_state(request: Request):
            self._logger.info("################################################################")
            self._logger.info("#                        < Job State >                         #")
            self._logger.info("################################################################")
            params = self._cvt_params(request)
            job_id = params.get('job-id')
            if not job_id:
                job_id = params.get('job_id')
            workflow_executor = self._get_task_executor(job_id)
            if not workflow_executor:
                return
            job_status = self._metric_service.extract_job_state(workflow_executor)
            return job_status

        @self.router.get(path='/workflow/working_state')
        async def call_working_state(request: Request):
            self._logger.info("################################################################")
            self._logger.info("#                      < Working State >                       #")
            self._logger.info("################################################################")
            is_working = self._metric_service.get_working_state()
            return is_working

        @self.router.websocket("/workflow/chat")
        async def websocket_endpoint(websocket: WebSocket):
            # REQ: HEADER {request_id, session_id}, BODY: {}
            self._logger.info("################################################################")
            self._logger.info("#                        < Web Socket >                        #")
            self._logger.info("################################################################")
            connection_id = str(uuid.uuid4())

            await self._ws_manager.connect(websocket, connection_id)
            session_id = 'session-id'
            wf_id = getWorkflowId()
            store_pack = self._set_store_pack(wf_id, None)
            stream_handler = WebStreamHandler(self._logger, self._ws_manager, store_pack)
            await stream_handler.run_stream(connection_id)
