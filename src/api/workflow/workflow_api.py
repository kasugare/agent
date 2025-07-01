#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.service.meta.meta_load_service import MetaLoadService
from api.workflow.service.data.data_store_service import DataStoreService
from api.workflow.service.execute.workflow_execution_orchestrator import WorkflowExecutionOrchestrator
from multiprocessing import Process, Queue
from typing import Dict, Any
from abc import abstractmethod
from fastapi import APIRouter
from threading import Thread
import json
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
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, logger=None, db_conn=None):
        super().__init__(logger, tags=['serving'])
        self._datastore = DataStoreService(logger)
        self._meta_service = MetaLoadService(logger, self._datastore)
        self._job_Q = Queue()

    def __del__(self):
        print("DEL DEL")
        self._job_Q.put_nowait("TERMINATION")
        self._job_Q.join()

    def setup_routes(self):
        @self.router.post(path='/workflow/meta')
        async def create_workflow(workflow) -> None:
            wf_meta = json.loads(workflow)
            self._meta_service.change_wf_meta(wf_meta)
            # return self._meta_service.get_dag()

        @self.router.post(path='/workflow/run')
        async def call_chained_model_service(request: Dict[str, Any]):
            if request and 'request_id' in list(request.keys()):
                request_id = request.pop('request_id')
            else:
                request_id = "AUTO_%X" %(int(time.time() * 10000))

            request['request_id'] = request_id
            workflow_engine = WorkflowExecutionOrchestrator(self._logger, self._datastore, self._job_Q)
            # workflow_engine = WorkflowExecutionService(self._logger, self._datastore)
            executor = Thread(target=workflow_engine.run_workflow, args=(request,))
            executor.start()
            print("대기")
            executor.join()

            # result = workflow_engine.run_workflow(request)
            return {"result": "result"}

        @self.router.get(path='/workflow/datapool')
        async def call_data_pool():
            self._logger.debug("---------------------------------< Data Pool >---------------------------------")
            data_pool = self._datastore.get_service_data_pool()
            for k, v in data_pool.items():
                self._logger.debug(f" - {k} : \t{v}")
            return data_pool
