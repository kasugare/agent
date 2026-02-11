#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.service.execute.workflow_executor import WorkflowExecutor
from api.workflow.control.execute.task_state import TaskState


class MetricService:
    def __init__(self, logger):
        self._logger = logger

    def _cvt_params(self, request, body={}):
        params = {}
        if request and request.headers:
            params.update(dict(request.headers))
        if body:
            params.update(dict(body))
        self._logger.debug("Input Params")
        for k, v in params.items():
            self._logger.warn(f" - {k}: {v}")
        return params

    def extract_io_data(self, datastore):
        # for wf_id, datastore in data_service_pool.items():
        # self._logger.info(f"<{wf_id}>")
        data_pool = datastore.get_service_data_pool_service()
        d = dict(sorted(data_pool.items()))
        for k, v in d.items():
            splited_key = k.split(".")
            in_type = splited_key[0]
            service_id = (".").join(splited_key[1:])
            self._logger.info(f"  L [{in_type}] {service_id} : {v}")
        return data_pool

    def extract_active_dag(self, workflow_executor):
        act_meta = workflow_executor.get_act_meta()
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

    def extract_active_task_pool(self, workflow_executor):
        act_meta = workflow_executor.get_act_meta()
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

    def extract_job_state(self, workflow_executor):
        def is_completed(task_state: dict):
            if task_state in [TaskState.COMPLETED, TaskState.SKIPPED]:
                return True
            return False

        def has_error(task_state: dict):
            if task_state in [TaskState.FAILED]:
                return True
            return False

        def is_stopped(task_state: dict):
            if task_state in [TaskState.STOPPED]:
                return True
            return False

        act_meta = workflow_executor.get_act_meta()
        act_task_map = act_meta.get('act_task_map')
        if not act_task_map:
            return {}

        job_status = {}
        task_state = {}
        for task_id, task_obj in act_task_map.items():
            service_id = task_obj.get_service_id()
            task_state[task_id] = task_obj.get_state()
        job_status["task_state"] = task_state

        is_completed = all(is_completed(task_state) for task_state in task_state.values())
        if is_completed:
            job_status["status"] = "COMPLETED"

        has_error = all(has_error(task_state) for task_state in task_state.values())
        if has_error:
            job_status["status"] = "FAILED"

        is_stopped = all(is_stopped(task_state) for task_state in task_state.values())
        if is_stopped:
            job_status["status"] = "STOPPED"

        processing_time = workflow_executor.get_processing_time()
        job_status["processing_time"] = processing_time

        input_params = workflow_executor.get_params()
        job_status['params'] = input_params

        for state_key, state_value in job_status.items():
            if isinstance(state_value, dict):
                self._logger.debug(f" - {state_key}")
                for k, v in state_value.items():
                    self._logger.debug(f"    L {k}: {v}")
            else:
                self._logger.debug(f" - {state_key}: {state_value}")
        return job_status

    def get_working_state(self):
        result = {
            "is_working": False
        }
        return result




