#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.service.meta.meta_load_service import MetaLoadService
from api.workflow.service.data.data_store_service import DataStoreService
from api.workflow.service.task.task_load_service import TaskLoadService
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
        super().__init__(logger, tags=['serving'])
        self._job_Q = Queue()
        self._datastore = DataStoreService(logger)
        self._taskstore = TaskLoadService(logger, self._datastore)
        self._metastore = MetaLoadService(logger, self._datastore)
        self._workflow_executor = WorkflowExecutor(logger, self._datastore, self._metastore, self._taskstore, self._job_Q)
        self._ws_manager = WSConnectionManager(logger)

    def setup_routes(self):
        @self.router.post(path='/workflow/meta', response_model=BaseResponse[schema.ResCreateWorkflow])
        async def create_workflow(headers: HeaderModel = Depends(get_headers), req: schema.ReqCreateWorkflow = ...):
            self._logger.info("################################################################")
            self._logger.info("#                         < Set Meta >                         #")
            self._logger.info("################################################################")
            self._datastore.clear()
            wf_meta = req.meta

            if not wf_meta:
                self._logger.warn("InvalidInputException: invalid workflow meta")
                raise InvalidInputException(err_detail="Invalid workflow meta")
            self._metastore.change_wf_meta(wf_meta)
            return {}


        @self.router.get(path='/workflow/clear', response_model=BaseResponse[schema.ResCallDataClear])
        async def call_data_clear(headers: HeaderModel = Depends(get_headers), req: schema.ReqCallDataClear = ...):
            self._logger.info("################################################################")
            self._logger.info("#                         < Clear All >                        #")
            self._logger.info("################################################################")
            self._datastore.clear()
            return {}

        @self.router.post(path='/workflow/run', response_model=BaseResponse[schema.ResCallChainedModelService])
        async def call_chained_model_service(headers: HeaderModel = Depends(get_headers), req: schema.ReqCallChainedModelService = ...):
            # REQ: HEADER {request_id, session_id}, BODY: {from(opt), to(opt), question: "질의"}
            self._logger.info("################################################################")
            self._logger.info("#                            < RUN >                           #")
            self._logger.info("################################################################")
            start_node, end_node, params = req.from_node, req.to_node, req.parameter
            try:
                result = self._workflow_executor.run_workflow(params, start_node, end_node)
                response = {
                    "result": {
                        "answer": result
                    }
                }
            except NotDefinedWorkflowMetaException as e:
                raise NotDefinedMetaException(err_detail="Not defined workflow meta")

            except AttributeError as e:
                raise InvalidInputException(err_detail="Not defined node_id(s)")
            return response

        @self.router.get(path='/workflow/metapack')
        async def call_meta_pack():
            self._logger.info("################################################################")
            self._logger.info("#                         < Meta Pack >                        #")
            self._logger.info("################################################################")
            meta_pack = self._datastore.get_meta_pack_service()
            for k, v in meta_pack.items():
                self._logger.debug(f" - {k} : \t{v}")
            return meta_pack

        # @self.router.get(path='/workflow/datapool', response_model=BaseResponse[schema.ResCallDataPool])
        # async def call_data_pool(headers: HeaderModel = Depends(get_headers), req: schema.ReqCallDataPool = ...):
        @self.router.get(path='/workflow/datapool')
        async def call_data_pool(request):
            self._logger.info("################################################################")
            self._logger.info("#                         < Data Pool >                        #")
            self._logger.info("################################################################")
            data_pool = self._datastore.get_service_data_pool_service()
            for k, v in data_pool.items():
                splited_key = k.split(".")
                in_type = splited_key[0]
                service_id = (".").join(splited_key[0:])
                self._logger.warn(f"[{in_type}] {service_id} : {v}")
            # response = {
            #     'result': {
            #         'node_id': req.node_id,
            #         'data': data_pool,
            #         'timestamp': ""
            #     }
            # }
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
            return act_meta

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
            return act_task_map

        @self.router.websocket("/workflow/chat")
        async def websocket_endpoint(websocket: WebSocket):
            # REQ: HEADER {request_id, session_id}, BODY: {}
            self._logger.info("################################################################")
            self._logger.info("#                        < Web Socket >                        #")
            self._logger.info("################################################################")
            connection_id = str(uuid.uuid4())

            await self._ws_manager.connect(websocket, connection_id)
            stream_handler = WebStreamHandler(self._logger, self._ws_manager, self._datastore, self._metastore, self._taskstore)
            await stream_handler.run_stream(connection_id)
