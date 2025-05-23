#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.control.execute.task_state import TaskState


class TaskStateManager:
    @staticmethod
    def can_transition(task, target_state):
        """현재 상태에서 목표 상태로 전환 가능한지 확인"""
        valid_transitions = {
            TaskState.PENDING: [TaskState.SCHEDULED, TaskState.CANCELED, TaskState.SKIPPED],
            TaskState.SCHEDULED: [TaskState.QUEUED, TaskState.CANCELED],
            TaskState.QUEUED: [TaskState.RUNNING, TaskState.CANCELED],
            TaskState.RUNNING: [TaskState.COMPLETED, TaskState.FAILED, TaskState.PAUSED, TaskState.TIMEOUT],
            TaskState.PAUSED: [TaskState.RUNNING, TaskState.CANCELED],
            TaskState.FAILED: [TaskState.RETRYING, TaskState.CANCELED],
        }

        return target_state in valid_transitions.get(task.state, [])

    @staticmethod
    def transition(task, target_state):
        """상태 전이 수행"""
        if TaskStateManager.can_transition(task, target_state):
            task.state = target_state
            return True
        return False