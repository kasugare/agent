#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .service.dag_meta_service import DagLoadService
from .workflow.workflow_manager import WorkflowManager
from typing import List, Dict, Optional, Any
from abc import ABC, abstractmethod
from fastapi import APIRouter
import traceback
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


class ServingProvider(BaseRouter):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, logger=None, db_conn=None):
        super().__init__(logger, tags=['serving'])
        self._dag_loader = DagLoadService(logger)
        self._dag_loader.start_background_loop()
        self._workflow_engine = WorkflowManager(logger)

    def setup_routes(self):
        @self.router.get(path='/set_meta')
        async def create_workflow(workflow) -> Dict:
            wf_config = json.loads(workflow)
            self._dag_loader.change_dag_meta(wf_config)
            return self._dag_loader.get_dag()

        @self.router.get(path='/call_api')
        async def call_chained_model_service() -> List[dict]:
            dag_meta = self._dag_loader.get_dag()
            dag_grape = self._dag_loader.get_edge_map()
            start_nodes = self._dag_loader.get_start_nodes()
            self._logger.warn(dag_meta)

            result = self._workflow_engine.run_workflow(dag_meta, dag_grape, start_nodes)
            result_set = []
            for node_id in result.keys():
                try:
                    result_set.append(result[node_id]['result'])
                except Exception as e:
                    self._logger.error(traceback.format_exc())
            self._logger.critical("Done")
            return result_set
