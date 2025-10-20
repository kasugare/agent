# !/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.control.execute.task_context import TaskContext
from api.workflow.control.execute.task_state import TaskState
from datetime import datetime

class Task(TaskContext):
    def __init__(self, logger, service_id, service_info):
        super().__init__(logger, service_id, service_info)
        self._logger = logger
        self.set_state(TaskState.PENDING)
        self._start_time = None
        self._end_time = None

    def execute(self):
        try:
            self.set_state(TaskState.RUNNING)
            self._start_time = datetime.now()
            result = self._executor.run(self.get_params())
            self.set_result(result)
            self.set_state(TaskState.COMPLETED)
        except Exception as e:
            self.set_state(TaskState.FAILED)
            self.set_error(e)
            self._logger.error(e)
        finally:
            self._end_time = datetime.now()
        self._logger.debug(f"{self._start_time} - {self._end_time}")

    def cancel(self):
        if self._state in (TaskState.PENDING, TaskState.SCHEDULED, TaskState.QUEUED):
            self.set_state(TaskState.CANCELED)
            return True
        return False

    def print_service_info(self):
        def print_params(params_format):
            for params_info in params_format:
                param_name = params_info.get('key')
                value_type = params_info.get('type')
                required = params_info.get('required')
                self._logger.debug(f"          L  [{required}] param_name: {param_name} ({value_type}) ")

        def print_result(results_format):
            for result_info in results_format:
                param_name = result_info.get('key')
                value_type = result_info.get('type')
                self._logger.debug(f"          L  param_name:  {param_name}  ({value_type}) ")

        def print_connection():
            for k, v in self._conn_info.items():
                self._logger.debug(f"      L  {k}:\t{v}")

        self._logger.debug(f" - (common) task_type:\t {self.get_task_type()}")
        self._logger.debug(f" - (common) role:    \t {self.get_role()}")
        self._logger.debug(f" - (common) location:\t {self.get_location()}")
        self._logger.debug(f" - (common) node_type:\t {self.get_node_type()}")
        self._logger.debug(f" - (common) params_map")
        self._logger.debug(f" - (common) result_format")
        self._logger.debug(f" - (API) connection_info")