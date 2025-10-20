#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.service.execute.action_planner import ActionPlanningService
from api.workflow.control.execute.workflow_execution_orchestrator import WorkflowExecutionOrchestrator


class WorkflowExecutor:
    def __init__(self, logger, datastore, metastore, taskstore, job_Q, stream_Q=None):
        self._logger = logger
        self._datastore = datastore
        self._metastore = metastore
        self._taskstore = taskstore
        self._job_Q = job_Q
        self._stream_Q = stream_Q
        self._act_planner = ActionPlanningService(logger, self._datastore, self._metastore, self._taskstore)
        self._act_meta = {}

    def get_act_meta(self):
        return self._act_meta

    def run_workflow(self, context, start_node=None, end_node=None):
        act_meta_pack = self._act_planner.gen_action_meta_pack(start_node, end_node, context)

        self._act_meta = act_meta_pack
        if act_meta_pack.get('act_start_nodes'):
            workflow_engine = WorkflowExecutionOrchestrator(self._logger, self._datastore, act_meta_pack, self._job_Q, self._stream_Q)
            result = workflow_engine.run_workflow(context)
        else:
            self._logger.error(f"# Not generated task_map, check DAG meta")
            result = "# Not generated task_map, check DAG meta"
        return result