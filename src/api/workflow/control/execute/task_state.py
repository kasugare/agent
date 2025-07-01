#!/usr/bin/env python
# -*- coding: utf-8 -*-

from enum import Enum, auto


class TaskState(Enum):
    PENDING = auto()
    SCHEDULED = auto()
    QUEUED = auto()
    RUNNING = auto()
    COMPLETED = auto()

    FAILED = auto()
    CANCELED = auto()
    PAUSED = auto()
    TIMEOUT = auto()
    STOPPED = auto()

    BLOCKED = auto()
    RETRYING = auto()
    SKIPPED = auto()