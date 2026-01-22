# !/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.control.execute.task_context import TaskContext
from api.workflow.control.execute.task_state import TaskState
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from api.workflow.error_pool.error import ExceedExecutionRetryError
import time


class Task(TaskContext):
    def __init__(self, logger, service_id, service_info, timeout_config):
        super().__init__(logger, service_id, service_info, timeout_config)
        self._logger = logger
        self._start_dt = None
        self._end_dt = 0.0

        self.set_state(TaskState.PENDING)
        self.init_retry_count()

    def get_duration(self):
        duration = "%0.2f" %(self._end_dt - self._start_dt)
        return duration

    def _set_current_task_state(self):
        curr_state = self.get_state()
        if curr_state in [TaskState.QUEUED, TaskState.RUNNING]:
            self.set_state(TaskState.RUNNING)
        elif curr_state in [TaskState.TIMEOUT]:
            self.set_state(TaskState.RETRYING)

    def _set_start_time(self):
        if not self._start_dt:
            self._start_dt = time.time()

    def execute(self, timeout=0):
        executor = None
        sid = self.get_service_id()
        try:
            self._set_current_task_state()
            self._set_start_time()

            executor = ThreadPoolExecutor(max_workers=1)
            params = self.get_params()
            if isinstance(params, dict):
                future = executor.submit(self._executor.run, **params)
            elif isinstance(params, (list, tuple)):
                future = executor.submit(self._executor.run, *params)
            else:
                future = executor.submit(self._executor.run, params)
            if timeout == 0:
                timeout = self.get_timeout()
            self._logger.info(f"# {self.get_service_id()}: Run service execution, timeout: {timeout}")
            result = future.result(timeout=timeout)
            self.set_result(result)
            self.set_state(TaskState.COMPLETED)
        except TimeoutError as e:
            if executor:
                executor.shutdown(wait=False, cancel_futures=True)
            try:
                timeout = self.get_retry_timeout()
                self._logger.error(f"this task has timed out. it going to retry({self.get_current_retry_count()}/{self.get_max_retries()}), set timeout: {timeout}")
                self.set_error(e.__str__())
                self.set_state(TaskState.TIMEOUT)
                self.sleep_delay()
                self.execute(timeout)
            except ExceedExecutionRetryError as e:
                self._logger.error(f"this task has exceed retry. this task was be failed!")
                self.set_state(TaskState.FAILED)
                self.set_error(e)
        except Exception as e:
            import traceback
            print(traceback.print_exc())
            self._logger.error(e)
            self.set_state(TaskState.FAILED)
            self.set_error(e)
        finally:
            if executor:
                executor.shutdown(wait=False)
            self._end_dt = time.time()
        self._logger.debug(f" - Process Time: {self.get_duration()}/ms")

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