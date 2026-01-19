#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.conf_serving import getWorkflowId
from api.workflow.data_pool.service_pool import ServicePool
from api.workflow.data_pool.meta_service_pool import MetaServicePool
from api.workflow.service.meta.auto_meta_loader import AutoMetaLoader
from api.workflow.service.meta.wf_meta_parser import WorkflowMetaParser
from api.workflow.service.meta.prompt_meta_generator import PromptMetaGenerator
from api.workflow.service.execute.workflow_executor import WorkflowExecutor
from api.workflow.service.stream.web_stream_connection_manager import WSConnectionManager
from api.workflow.service.stream.web_stream_handler import WebStreamHandler
from api.workflow.protocol.schema import BaseResponse
from api.workflow.protocol.workflow_headers import HeaderModel, get_headers
from api.workflow.error_pool.error import NotDefinedWorkflowMetaException
from error.parent_exception import InvalidInputException
from error.parent_exception import NotDefinedMetaException
from fastapi import APIRouter, WebSocket, Depends
from multiprocessing import Queue
from abc import abstractmethod
from typing import Any
import api.workflow.protocol.workflow_schema as schema
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


class WorkflowEngine(BaseRouter):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, logger, db_conn=None):
        super().__init__(logger, tags=['Workflow Engine'])
        self._job_Q = Queue()
        self._ws_manager = WSConnectionManager(logger)
        self._meta_service_pool = MetaServicePool(logger)
        self._run_auto_meta_loader()

    def _run_auto_meta_loader(self):
        auto_meta_loader = AutoMetaLoader(self._logger, self._meta_service_pool)


    def setup_routes(self):
        @self.router.post(path='/workflow/meta', response_model=BaseResponse[schema.ResCreateWorkflow])
        async def create_workflow(headers: HeaderModel = Depends(get_headers), request: schema.ReqCreateWorkflow = ...):
            self._logger.info("################################################################")
            self._logger.info("#                         < Set Meta >                         #")
            self._logger.info("################################################################")
            request_id = headers.request_id
            wf_meta = request.meta
            # self._metaloader.change_wf_meta(wf_meta, request_id)
            if not wf_meta:
                self._logger.warn("InvalidInputException: invalid workflow meta")
                raise InvalidInputException(err_detail="Invalid workflow meta")
            meta_loader = WorkflowMetaParser(self._logger)
            meta_loader.set_meta(wf_meta, request_id)
            meta_pack = meta_loader.get_meta_pack()
            if meta_pack:
                wf_id = meta_pack.get('workflow_id')
                self._store_map[wf_id] = {
                    "meta_pack": meta_pack,
                    "session": {
                        "{session_id}": {
                            "{req_id}": {
                                "io_pool": {},
                                "task_pool": {}
                            }
                        }
                    }
                }
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
            self._metaloader.change_wf_meta(wf_meta_template, request_id)
            response = {}
            try:
                result = self._workflow_executor.run_workflow(params)
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
            self._datastore.clear()
            return {}

        @self.router.post(path='/workflow/run', response_model=BaseResponse[dict[str, Any]])
        async def call_chained_model_service(headers: HeaderModel = Depends(get_headers), request: schema.ReqCallChainedModelService = ...):
            # REQ: HEADER {request_id, session_id}, BODY: {from(opt), to(opt), question: "질의"}
            self._logger.info("################################################################")
            self._logger.info("#                            < RUN >                           #")
            self._logger.info("################################################################")
            start_node, end_node, params = request.from_node, request.to_node, request.parameter
            response = {}
            try:
                # current_wf_meta = self._datastore.get_wf_meta_service()
                # self._datastore.clear()
                # self._metaloader.change_wf_meta(current_wf_meta, "run")
                req_id = headers.request_id
                session_id = headers.session_id
                result = self._workflow_executor.run_workflow(params, start_node, end_node)
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
        async def call_chained_model_service(headers: HeaderModel = Depends(get_headers), request: schema.ReqCallChainedModelService = ...):
            # REQ: HEADER {request_id, session_id}, BODY: {from(opt), to(opt), question: "질의"}
            self._logger.info("################################################################")
            self._logger.info("#                        < INFERENCE >                         #")
            self._logger.info("################################################################")

            params = request.parameter
            response = {}
            try:
                req_id = headers.request_id
                session_id = headers.session_id
                wf_id = getWorkflowId()
                if not session_id:
                    session_id = req_id

                workflow_executor = WorkflowExecutor(self._logger, self._datastore, self._job_Q)
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

        @self.router.get(path='/workflow/metapack')
        async def call_meta_pack():
            self._logger.info("################################################################")
            self._logger.info("#                         < Meta Pack >                        #")
            self._logger.info("################################################################")
            meta_pack = self._metaloader.get_meta_pack()
            for k, v in meta_pack.items():
                self._logger.debug(f" - {k} : \t{v}")
            return meta_pack

        # @self.router.get(path='/workflow/datapool', response_model=BaseResponse[schema.ResCallDataPool])
        # async def call_data_pool(headers: HeaderModel = Depends(get_headers), req: schema.ReqCallDataPool = ...):
        @self.router.get(path='/workflow/datapool')
        async def call_data_pool():
            self._logger.info("################################################################")
            self._logger.info("#                         < Data Pool >                        #")
            self._logger.info("################################################################")
            data_pool = self._datastore.get_service_data_pool_service()
            for k, v in data_pool.items():
                splited_key = k.split(".")
                in_type = splited_key[0]
                service_id = (".").join(splited_key[1:])
                self._logger.debug(f"[{in_type}] {service_id} : {v}")
            return data_pool

        @self.router.get(path='/workflow/act_dag')
        async def call_active_dag():
            self._logger.info("################################################################")
            self._logger.info("#                        < Active DAG >                        #")
            self._logger.info("################################################################")
            act_meta = self._workflow_executor.get_act_meta()
            for k, v in act_meta.items():
                self._logger.info(f" - {k}")
                if isinstance(v, dict):
                    for kk, vv in v.items():
                        self._logger.debug(f" \t- {kk}: {vv}")
                elif isinstance(v, list):
                    for l in v:
                        self._logger.debug(f" \t- {l}")
                else:
                    self._logger.debug(f" \t- {v}")
                self._logger.debug("*" * 200)
            # return act_meta

        @self.router.get(path='/workflow/tasks')
        async def call_task_pool():
            self._logger.info("################################################################")
            self._logger.info("#                       < Active Tasks >                       #")
            self._logger.info("################################################################")
            act_meta = self._workflow_executor.get_act_meta()
            act_task_map = act_meta.get('act_task_map')
            if not act_task_map:
                return
            for task_id, task_obj in act_task_map.items():
                self._logger.info(f" - {task_id}")
                service_id = task_obj.get_service_id()

                state = task_obj.get_state()
                env = task_obj.get_env_params()
                params = task_obj.get_params()
                result = task_obj.get_result()
                error = task_obj.get_error()
                node_type = task_obj.get_node_type()
                self._logger.debug(f"\t- service_id: {service_id}")
                self._logger.debug(f"\t- state:      {state}")
                self._logger.debug(f"\t- env:        {env}")
                self._logger.debug(f"\t- params:     {params}")
                self._logger.debug(f"\t- result:     {result}")
                self._logger.debug(f"\t- Error:      {error}")
                self._logger.debug(f"\t- node_type:  {node_type}")
                task_obj.print_service_info()
                self._logger.debug("*" * 100)
            # return act_task_map

        @self.router.websocket("/workflow/chat")
        async def websocket_endpoint(websocket: WebSocket):
            # REQ: HEADER {request_id, session_id}, BODY: {}
            self._logger.info("################################################################")
            self._logger.info("#                        < Web Socket >                        #")
            self._logger.info("################################################################")
            connection_id = str(uuid.uuid4())

            await self._ws_manager.connect(websocket, connection_id)
            stream_handler = WebStreamHandler(self._logger, self._ws_manager, self._datastore)
            await stream_handler.run_stream(connection_id)
