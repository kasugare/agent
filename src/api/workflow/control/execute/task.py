#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.control.execute.task_context import TaskContext
from api.workflow.control.execute.task_state import TaskState
from datetime import datetime


class Task(TaskContext):
    def __init__(self, logger, datastore, service_id, node_info):
        super().__init__(logger, datastore, service_id, node_info)
        self._logger = logger

        self._state = self.set_state()
        self._error = None
        self._start_time = None
        self._end_time = None
        self._params = {}
        self._result = None

        self._job_Q = None

    def set_params(self, params=None):
        self._params = params

    def _set_result(self, result):
        self._result = result

    def get_params(self):
        return self._params

    def set_state(self, state=TaskState.PENDING):
        self._state = state
        return state

    def get_state(self):
        return self._state

    def get_error(self):
        return self._error

    def set_job_Q(self, job_Q):
        self._job_Q = job_Q

    def set_task(self, name, executor, **kwargs):
        self._task_name = name
        self._executor = executor
        self.set_params(kwargs)

    def get_result(self):
        return self._result

    def execute(self):
        try:
            # self._params = params
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

        if self._job_Q:
            self._job_Q.put_nowait(self.get_service_id())


    def cancel(self):
        if self._state in (TaskState.PENDING, TaskState.SCHEDULED, TaskState.ASSIGNED, TaskState.QUEUED):
            self._state = TaskState.CANCELED
            return True
        return False