#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ailand.common.logger import Logger
from recipe.recipe_manager import DAGLoader
from workflow.workflow_executor import WorkflowExecutor
import traceback
import asyncio
import json


class ServingProvider:
    def __init__(self):
        self._logger = Logger().getLogger()
        self._workflow_config = None

    def load_dag(self, config_dir: str, dag_filename: str = None):
        if not dag_filename:
            dag_filename = 'test_dag.json'

        self._dag_loader = DAGLoader(self._logger, config_dir)
        workflow_config = self._dag_loader.load_dag(dag_filename)
        self._workflow_config = workflow_config
        return workflow_config

    def get_workflow(self):
        if not self._workflow_config:
            raise Exception(f"not exist workflow, ")
        return self._workflow_configsc

    async def run_executor(self, executor):
        results = await executor.execute_workflow()
        return results

    def do_process(self):
        config_dir = '/Users/hanati/workspace/model_serving/test/serving_engine/recipe'
        workflow_config = service.load_dag(config_dir)

        self._logger.info("# Step 2: load workflow config(DAG)")
        executor = WorkflowExecutor(self._logger, workflow_config)
        results = asyncio.run(self.run_executor(executor))


        self._logger.info("# Step 3: show result form workflow pipeline")
        # self._logger.debug(json.dumps(results, indent=2))


# async def run_workflow():
#     service = ServingProvider()
#     await service.do_process()

# 메인 실행
if __name__ == "__main__":
    # asyncio.run(run_workflow())
    service = ServingProvider()
    service.do_process()