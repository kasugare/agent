#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.service.execute.action_planner import ActionPlanningService
from api.workflow.control.execute.workflow_execution_orchestrator import WorkflowExecutionOrchestrator
from api.workflow.error_pool.error import InvalidInputException, NotDefinedWorkflowMetaException
from datetime import datetime, timezone, timedelta
import time


class WorkflowExecutor:
    def __init__(self, logger, store_pack, stream_Q=None):
        self._logger = logger
        self._store_pack = store_pack
        self._datastore = store_pack.get('datastore', {})
        self._metastore = store_pack.get('metastore', {})
        self._stream_Q = stream_Q
        self._start_dt = 0
        self._end_dt = 0
        self._init_data_store()

    def _init_data_store(self):
        meta_pack = self._metastore.get_meta_pack_service()
        self._datastore.set_init_service_params_service(meta_pack.get('edges_info'))
        self._datastore.set_init_nodes_env_params_service(meta_pack.get('nodes_env_value_map'))
        self._datastore.set_init_nodes_asset_params_service(meta_pack.get('nodes_asset_value_map'))
        self._act_planner = ActionPlanningService(self._logger, meta_pack, self._store_pack)

    def _set_start_ts(self):
        self._start_dt = int(time.time() * 1000)

    def _set_end_ts(self):
        self._end_dt = int(time.time() * 1000)

    def get_processing_time(self):
        duration_ts = self._end_dt - self._start_dt
        utc8 = timezone(timedelta(hours=8))
        start_dt = datetime.fromtimestamp(self._start_dt/1000, tz=utc8)
        end_dt = datetime.fromtimestamp(self._end_dt/1000, tz=utc8)
        processing_time = {
            "start_ts": self._start_dt,
            "end_ts": self._end_dt,
            "start_dt": start_dt.strftime('%Y%m%d%H%M%S'),
            "end_dt": end_dt.strftime('%Y%m%d%H%M%S'),
            "duration_ts": duration_ts / 1000
        }
        return processing_time

    def run_workflow(self, params):
        start_node = params.get('from_node', None)
        end_node = params.get('to_node', None)
        try:
            act_meta_pack = self._act_planner.gen_action_meta_pack(start_node, end_node, params)
            # return

            if act_meta_pack.get('act_start_nodes'):
                workflow_engine = WorkflowExecutionOrchestrator(self._logger, self._store_pack, act_meta_pack, self._stream_Q)
                result = workflow_engine.run_workflow(params)
            else:
                self._logger.error(f"# Not generated task_map, check DAG meta")
                result = "# Not generated task_map, check DAG meta"
            self._set_end_ts()
            return result
        except NotDefinedWorkflowMetaException as e:
            self._set_end_ts()
            raise NotDefinedWorkflowMetaException
        except InvalidInputException as e:
            self._set_end_ts()
            raise AttributeError