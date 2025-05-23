#!/usr/bin/env python
# -*- coding: utf-8 -*-

from enum import Enum, auto
from datetime import datetime

class TaskState(Enum):
    PENDING = auto()    # 초기 상태
    SCHEDULED = auto()  # 실행 예약됨
    QUEUED = auto()     # 실행 큐에 추가됨
    RUNNING = auto()    # 실행 중
    COMPLETED = auto()  # 성공적 완료
    FAILED = auto()     # 실패
    CANCELED = auto()   # 취소됨
    PAUSED = auto()     # 일시 중지
    TIMEOUT = auto()    # 제한 시간 초과
    BLOCKED = auto()    # 진행 불가
    RETRYING = auto()   # 재시도 중
    SKIPPED = auto()    # 건너뜀


class Task:
    def __init__(self, name, function, **kwargs):
        self.name = name
        self.function = function
        self.kwargs = kwargs
        self.state = TaskState.PENDING
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None

    def execute(self):
        try:
            self.state = TaskState.RUNNING
            self.start_time = datetime.now()
            self.result = self.function(**self.kwargs)
            self.state = TaskState.COMPLETED
        except Exception as e:
            self.state = TaskState.FAILED
            self.error = e
        finally:
            self.end_time = datetime.now()
            print(f"{self.state} : {self.start_time} - {self.end_time}")

    def cancel(self):
        if self.state in (TaskState.PENDING, TaskState.SCHEDULED, TaskState.QUEUED):
            self.state = TaskState.CANCELED
            return True
        return False


class WorkflowEngine:
    def __init__(self):
        self.tasks = {}

    def add_task(self, task):
        self.tasks[task.name] = task

    def execute_workflow(self):
        for name, task in self.tasks.items():
            if task.state == TaskState.PENDING:
                task.state = TaskState.SCHEDULED
                # 실행 로직...

    def get_tasks_by_state(self, state):
        return [task for task in self.tasks.values() if task.state == state]

    def get_failed_tasks(self):
        return self.get_tasks_by_state(TaskState.FAILED)


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
            # 기타 가능한 전이...
        }

        return target_state in valid_transitions.get(task.state, [])

    @staticmethod
    def transition(task, target_state):
        """상태 전이 수행"""
        is_changeable = TaskStateManager.can_transition(task, target_state)
        print(f" - {task.state} \t-->\t{target_state}\t: {is_changeable}", )
        if is_changeable:
            task.state = target_state
            return True
        return False


def sample_task(x, y):
    return x + y



task = Task("addition", sample_task, x=5, y=10)

# 상태 변경
TaskStateManager.transition(task, TaskState.PENDING)
TaskStateManager.transition(task, TaskState.SCHEDULED)
TaskStateManager.transition(task, TaskState.QUEUED)
TaskStateManager.transition(task, TaskState.RUNNING)

# 실행
task.execute()  # 내부적으로 RUNNING -> COMPLETED 또는 FAILED로 전환

# 상태 확인
if task.state == TaskState.COMPLETED:
    print(f"Task completed with result: {task.result}")
elif task.state == TaskState.FAILED:
    print(f"Task failed with error: {task.error}")