#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Optional, TextIO
import fcntl
import time
import os


class FileLock:
    def __init__(self, lock_file_path: str = None, timeout: float = 5.0):
        self.lock_file_path = lock_file_path
        self.timeout = timeout
        self.lock_file = None
        self._acquired = False

    def __enter__(self):
        start_time = time.time()
        os.makedirs(os.path.dirname(self.lock_file_path), exist_ok=True)
        while not self.acquire():
            if time.time() - start_time > self.timeout:
                raise TimeoutError("Could not acquire lock")
            time.sleep(0.1)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    def acquire(self) -> bool:
        if self._acquired:
            return True

        try:
            self.lock_file = open(self.lock_file_path, 'w')
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._acquired = True
            return True
        except BlockingIOError:
            if self.lock_file:
                self.lock_file.close()
            return False

    def release(self):
        if self.lock_file and self._acquired:
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
            self.lock_file.close()
            self._acquired = False

    @property
    def is_locked(self) -> bool:
        """현재 잠금 상태 확인"""
        return self._acquired
