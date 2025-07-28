#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.service.meta.meta_load_service import MetaLoadService
from api.workflow.service.data.data_store_service import DataStoreService
from api.workflow.service.task.task_load_service import TaskLoadService
from api.workflow.service.execute.action_planner import ActionPlanningService
from api.workflow.service.execute.workflow_execution_orchestrator import WorkflowExecutionOrchestrator
from multiprocessing import Process, Queue
from typing import Dict, Any
from abc import abstractmethod
from fastapi import APIRouter
import time
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


class WorkflowEngine(BaseRouter):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, logger=None, db_conn=None):
        super().__init__(logger, tags=['serving'])
        self._datastore = DataStoreService(logger)
        self._taskstore = TaskLoadService(logger, self._datastore)
        self._metastore = MetaLoadService(logger, self._datastore, self._taskstore)
        self._act_planner = ActionPlanningService(logger, self._datastore, self._metastore, self._taskstore)
        self._job_Q = Queue()

    def setup_routes(self):
        @self.router.post(path='/workflow/meta')
        async def create_workflow(workflow) -> None:
            wf_meta = json.loads(workflow)
            self._metastore.change_wf_meta(wf_meta)
            # return self._metastore.get_dag()

        @self.router.post(path='/workflow/run')
        async def call_chained_model_service(request: Dict[str, Any]):
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

            act_meta_pack = self._act_planner.gen_action_meta_pack(start_node, end_node, request)
            if act_meta_pack.get('act_start_nodes'):
                workflow_engine = WorkflowExecutionOrchestrator(self._logger, self._datastore, act_meta_pack, self._job_Q)
                result = workflow_engine.run_workflow(request)
            else:
                self._logger.error(f"# Not generated task_map, check DAG meta")
                result = "# Not generated task_map, check DAG meta"
            return {"result": result}

        @self.router.get(path='/workflow/datapool')
        async def call_data_pool():
            self._logger.debug("-------------------------< Data Pool >-------------------------")
            data_pool = self._datastore.get_service_data_pool_service()
            for k, v in data_pool.items():
                self._logger.debug(f" - {k} : \t{v}")
            return data_pool

        @self.router.get(path='/workflow/state')
        async def call_task_pool():
            self._logger.debug("-------------------------< Data Pool >-------------------------")
            data_pool = self._datastore.get_service_data_pool_service()
            for k, v in data_pool.items():
                self._logger.debug(f" - {k} : \t{v}")
            return data_pool