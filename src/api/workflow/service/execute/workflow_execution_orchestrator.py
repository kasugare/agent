#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.control.execute.execution_flow_controller import ExecutionFlowController
from api.workflow.control.execute.task_generator import TaskGenerator
from multiprocessing import Queue


class WorkflowExecutionOrchestrator:
    def __init__(self, logger, datastore):
        self._logger = logger
        self._datastore = datastore
        self._job_Q = Queue()
        self._flow_controller = ExecutionFlowController(logger, datastore, self._job_Q)
        self._task_generator = TaskGenerator(logger, datastore)



    def run_workflow(self, request_params):
        self._logger.critical(f" # user params: {request_params}")
        # self._flow_controller.do_process(request_params)
        self._task_generator.make_tasks()
