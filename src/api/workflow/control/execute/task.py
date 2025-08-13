#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.control.execute.task_context import TaskContext
from api.workflow.control.execute.task_state import TaskState
from datetime import datetime


class Task(TaskContext):
    def __init__(self, logger, service_id, service_info):
        super().__init__(logger, service_id, service_info)
        self._logger = logger

        self._state = self.set_state()
        self._error = None
        self._start_time = None
        self._end_time = None
        self._env_params = {}
        self._params = {}
        self._result = None

    def set_env_params(self, env_params=None):
        self._env_params = env_params
        executor = self.get_executor()
        executor.set_env(env_params)

    def set_params(self, params=None):
        self._params = params

    def _set_result(self, result):
        self._result = result

    def get_env_params(self):
        return self._env_params

    def get_params(self):
        return self._params

    def set_state(self, state=TaskState.PENDING):
        self._state = state
        return state

    def get_state(self):
        return self._state

    def get_error(self):
        return self._error

    def set_task(self, task_name, executor, **kwargs):
        self._task_name = task_name
        self._executor = executor
        self.set_params(kwargs)

    def get_result(self):
        return self._result

    def execute(self):
        try:
            self._state = TaskState.RUNNING
            self._start_time = datetime.now()
            result = self._executor.run(self._params)
            self._set_result(result)
            self._state = TaskState.COMPLETED
        except Exception as e:
            self._state = TaskState.FAILED
            self._error = e
            self._logger.error(e)
        finally:
            self._end_time = datetime.now()
        self._logger.debug(f"{self._start_time} - {self._end_time}")

    def cancel(self):
        if self._state in (TaskState.PENDING, TaskState.SCHEDULED, TaskState.QUEUED):
            self._state = TaskState.CANCELED
            return True
        return False