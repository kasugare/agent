#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.control.execute.task_state import TaskState
from datetime import datetime


class Task:
    def __init__(self, logger, service_id, datastore):
        self._logger = logger
        self._service_id = service_id
        self._datastore = datastore

        self._state = self.set_state()
        self._task_name = None
        self._executor = None

        self._executor_meta = None
        self._params = None
        self._result = None
        self._error = None
        self._start_time = None
        self._end_time = None

    def set_state(self, state=TaskState.PENDING):
        self._state = state
        return state

    def get_state(self):
        return self._state

    def set_task(self, name, executor, **kwargs):
        self._task_name = name
        self._executor = executor
        self._params = kwargs

    def get_result(self):
        return self._result

    def execute(self):
        try:
            self._state = TaskState.RUNNING
            self._start_time = datetime.now()
            self._result = self._executor.run(**self._params)
            self._state = TaskState.COMPLETED
        except Exception as e:
            self._state = TaskState.FAILED
            self._error = e
        finally:
            self._end_time = datetime.now()

    def cancel(self):
        if self._state in (TaskState.PENDING, TaskState.SCHEDULED, TaskState.QUEUED):
            self._state = TaskState.CANCELED
            return True
        return False