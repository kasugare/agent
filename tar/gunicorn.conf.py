#!/usr/bin/env python
# -*- coding: utf-8 -*-

import multiprocessing
import resource
import os

bind = "0.0.0.0:8080"
workers = 1
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 5000
keepalive = 3
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
# preload_app = True

def on_starting(server):
    """서버 시작 시 실행"""
    multiprocessing.current_process().name = 'main'

def when_ready(server):
    """서버가 요청을 받을 준비가 됐을 때"""
    # 메인 프로세스의 PID 저장
    server._worker_pid = os.getpid()

def pre_fork(server, worker):
    """워커 포크 전"""
    pass

def post_fork(server, worker):
    """워커 포크 후"""
    # 워커 프로세스의 상태 초기화
    multiprocessing.current_process().name = f'worker-{worker.pid}'

def worker_exit(server, worker):
    print("""워커 종료 시""")
    # 리소스 정리
    try:
        multiprocessing.resource_tracker._resource_tracker._fd = None
    except Exception:
        pass

def on_starting(server):
    # 파일 디스크립터 제한 증가
    resource.setrlimit(resource.RLIMIT_NOFILE, (65536, 65536))
