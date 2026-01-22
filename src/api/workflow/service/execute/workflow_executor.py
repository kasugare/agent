#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.service.execute.action_planner import ActionPlanningService
from api.workflow.control.execute.workflow_execution_orchestrator import WorkflowExecutionOrchestrator
from api.workflow.error_pool.error import InvalidInputException, NotDefinedWorkflowMetaException


class WorkflowExecutor:
    def __init__(self, logger, metastore, datastore, job_Q, stream_Q=None):
        self._logger = logger
        self._datastore = datastore
        self._job_Q = job_Q
        self._stream_Q = stream_Q

        meta_pack = metastore.get_meta_pack_service()
        datastore.set_init_service_params_service(meta_pack.get('edges_info'))
        datastore.set_init_nodes_env_params_service(meta_pack.get('nodes_env_value_map'))
        datastore.set_init_nodes_asset_params_service(meta_pack.get('nodes_asset_value_map'))

        self._act_planner = ActionPlanningService(logger, meta_pack, datastore)
        self._act_meta = {}

    def get_act_meta(self):
        return self._act_meta

    def run_workflow(self, params, start_node=None, end_node=None):
        try:
            act_meta_pack = self._act_planner.gen_action_meta_pack(start_node, end_node, params)
            self._act_meta = act_meta_pack

            if act_meta_pack.get('act_start_nodes'):
                workflow_engine = WorkflowExecutionOrchestrator(self._logger, self._datastore, act_meta_pack, self._job_Q, self._stream_Q)
                result = workflow_engine.run_workflow(params)
            else:
                self._logger.error(f"# Not generated task_map, check DAG meta")
                result = "# Not generated task_map, check DAG meta"
            return result
        except NotDefinedWorkflowMetaException as e:
            raise NotDefinedWorkflowMetaException
        except InvalidInputException as e:
            raise AttributeError