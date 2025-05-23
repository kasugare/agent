#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.serving.service.task_io_service import TaskIOService
from api.serving.service.dag_meta_service import DagLoadService
from api.serving.service.workflow_execution_service import WorkflowExecutionService
from api.serving.service.JobTaskExecutor import JobTaskExecutor
from typing import List, Dict, Optional, Any
from abc import ABC, abstractmethod
from fastapi import APIRouter
import traceback
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


class ServingProvider(BaseRouter):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, logger=None, db_conn=None):
        super().__init__(logger, tags=['serving'])
        self._io_manager = TaskIOService(logger)
        self._dag_loader = DagLoadService(logger, self._io_manager)
        self._dag_loader.start_background_loop()

    def setup_routes(self):
        @self.router.get(path='/set_workflow')
        async def create_workflow(workflow) -> Dict:
            wf_config = json.loads(workflow)
            self._dag_loader.change_dag_meta(wf_config)
            return self._dag_loader.get_dag()

        @self.router.post(path='/run_workflow')
        async def call_chained_model_service(request: Dict[str, Any]):
            if request and 'request_id' in list(request.keys()):
                request_id = request.pop('request_id')
            else:
                request_id = "AUTO_%X" %(int(time.time() * 10000))
            request['request_id'] = request_id

            meta_pack = self._dag_loader.get_meta_pack()
            workflow_engine = JobTaskExecutor(self._logger, meta_pack)
            result = workflow_engine.do_process(request)
            # workflow_engine = WorkflowExecutionService(self._logger, meta_pack)

            # input_params = workflow_engine.extract_params(request)
            # workflow_engine.check_start_params(request)

            return {"result": result}

            if edges_grape:
                input_params = {"request_id": "1234567890", "src_stt": "test stt input data!!"}
                result = workflow_engine.run_workflow(input_params)
                result_set = []
                for node_id in result.keys():
                    try:
                        result_set.append(result[node_id]['result'])
                    except Exception as e:
                        self._logger.error(traceback.format_exc())
            else:
                result_set = [{
                    "status": "fail",
                    "error_pool": "DAG not exist"
                }]
            self._logger.critical("Done")
            return result_set

        @self.router.get(path='/add_func')
        async def add_function() -> None:
             pass

