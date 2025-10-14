#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.service.meta.meta_load_service import MetaLoadService
from api.workflow.service.data.data_store_service import DataStoreService
from api.workflow.service.task.task_load_service import TaskLoadService
from api.workflow.service.execute.workflow_executor import WorkflowExecutor
from api.workflow.service.stream.web_stream_connection_manager import WSConnectionManager
from api.workflow.service.stream.web_stream_handler import WebStreamHandler
from fastapi import APIRouter, WebSocket
from multiprocessing import Queue
from abc import abstractmethod
from typing import Dict, Any
import time
import json
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
        @self.router.post(path='/workflow/meta')
        async def create_workflow(workflow) -> None:
            self._logger.error("################################################################")
            self._logger.error("#                         < Set Meta >                         #")
            self._logger.error("################################################################")
            self._datastore.clear()
            wf_meta = json.loads(workflow)
            self._metastore.change_wf_meta(wf_meta)

        @self.router.get(path='/workflow/clear')
        async def call_data_clear():
            self._logger.error("################################################################")
            self._logger.error("#                         < Clear All >                        #")
            self._logger.error("################################################################")
            self._datastore.clear()

        @self.router.post(path='/workflow/run')
        async def call_chained_model_service(request: Dict[str, Any]):
            self._logger.error("################################################################")
            self._logger.error("#                            < RUN >                           #")
            self._logger.error("################################################################")
            start_node = request.get('from')
            if start_node:
                request.pop('from')
            end_node = request.get('to')
            if end_node:
                request.pop("to")
            if request and 'request_id' in list(request.keys()):
                request_id = request.pop('request_id')
            else:
                request_id = "AUTO_%X" %(int(time.time() * 10000))
            request['request_id'] = request_id
            result = self._workflow_executor.run_workflow(request, start_node, end_node)
            return {"result": result}

        @self.router.get(path='/workflow/metapack')
        async def call_meta_pack():
            self._logger.error("################################################################")
            self._logger.error("#                         < Meta Pack >                        #")
            self._logger.error("################################################################")
            meta_pack = self._datastore.get_meta_pack_service()
            for k, v in meta_pack.items():
                self._logger.debug(f" - {k} : \t{v}")
            return meta_pack

        @self.router.get(path='/workflow/datapool')
        async def call_data_pool():
            self._logger.error("################################################################")
            self._logger.error("#                         < Data Pool >                        #")
            self._logger.error("################################################################")
            data_pool = self._datastore.get_service_data_pool_service()
            for k, v in data_pool.items():
                self._logger.debug(f" - {k} : \t{v}")
            return data_pool

        @self.router.get(path='/workflow/act_dag')
        async def call_active_dag():
            self._logger.error("################################################################")
            self._logger.error("#                        < Active DAG >                        #")
            self._logger.error("################################################################")
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
            self._logger.error("################################################################")
            self._logger.error("#                       < Active Tasks >                       #")
            self._logger.error("################################################################")
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
            self._logger.error("################################################################")
            self._logger.error("#                        < Web Socket >                        #")
            self._logger.error("################################################################")
            connection_id = str(uuid.uuid4())

            await self._ws_manager.connect(websocket, connection_id)
            stream_handler = WebStreamHandler(self._logger, self._ws_manager, self._datastore, self._metastore, self._taskstore)
            await stream_handler.run_stream(connection_id)
