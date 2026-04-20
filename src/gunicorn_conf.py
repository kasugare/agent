#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.conf_system import getServerInfo
import multiprocessing
import resource
import os
import logging

# ============ 기본 설정 ============
server_info = getServerInfo()

# 바인딩
bind = server_info.get("bind", "0.0.0.0:8080")

# Worker 설정 (CPU 코어 기반)
default_workers = (multiprocessing.cpu_count() * 2) + 1
workers = server_info.get("workers", default_workers)

# Worker 클래스
worker_class = server_info.get("worker_class", "uvicorn.workers.UvicornWorker")

# 타임아웃 설정
timeout = server_info.get("timeout", 3600)
graceful_timeout = server_info.get("graceful_timeout", 30)
keepalive = server_info.get("keepalive", 5)

# 연결 설정
worker_connections = server_info.get("worker_connections", 10000)
backlog = server_info.get("backlog", 2048)  # 대기 큐 크기

# 워커 재시작 (메모리 누수 방지)
max_requests = server_info.get("max_requests", 5000)
max_requests_jitter = server_info.get("max_requests_jitter", 300)

# 로깅
accesslog = server_info.get("accesslog", "-")  # stdout
errorlog = server_info.get("errorlog", "-")  # stdout
loglevel = server_info.get("loglevel", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 프로세스 이름
proc_name = server_info.get("proc_name", "ailand-api")

# 성능 최적화
# worker_tmp_dir = "/dev/shm"  # 메모리 기반 임시 디렉토리 (리눅스)


# Preload (선택적)
# preload_app = True  # 메모리 절약하지만 코드 핫리로드 불가

# ============ 후크 함수들 ============

def on_starting(server):
    """서버 시작 시 실행"""
    # 메인 프로세스 이름 설정
    multiprocessing.current_process().name = 'gunicorn-master'

    # 파일 디스크립터 제한 증가
    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        resource.setrlimit(resource.RLIMIT_NOFILE, (65536, 65536))
        server.log.info(f"File descriptor limit increased: {soft} -> 65536")
    except Exception as e:
        server.log.warning(f"Failed to increase file descriptor limit: {e}")

    server.log.info(f"Starting Gunicorn with {workers} workers")
    server.log.info(f"Worker class: {worker_class}")


def when_ready(server):
    """서버가 요청을 받을 준비가 됐을 때"""
    # 메인 프로세스 PID 저장
    server._worker_pid = os.getpid()
    server.log.info(f"Server ready. Master PID: {os.getpid()}")
    server.log.info(f"Listening on: {bind}")


def pre_fork(server, worker):
    """워커 포크 전"""
    server.log.debug(f"Pre-fork: Preparing worker {worker.pid}")

    # Redis 연결 등 리소스 정리 (필요 시)
    # 예: 부모 프로세스의 DB 연결 닫기
    # if hasattr(server, '_db_connections'):
    #     for conn in server._db_connections:
    #         conn.close()


def post_fork(server, worker):
    """워커 포크 후"""
    # 워커 프로세스 이름 설정
    worker_name = f'gunicorn-worker-{worker.age}'
    multiprocessing.current_process().name = worker_name

    server.log.info(f"Worker spawned (pid: {worker.pid}, age: {worker.age})")

    # 워커별 초기화 작업 (필요 시)
    # 예: Redis 연결 재설정, 로거 재설정 등


def pre_exec(server):
    """exec 전 (바이너리 재시작 시)"""
    server.log.info("Forked child, re-executing.")


def worker_int(worker):
    """워커가 SIGINT 받았을 때"""
    worker.log.info(f"Worker received INT or QUIT signal (pid: {worker.pid})")


def worker_abort(worker):
    """워커가 SIGABRT 받았을 때 (타임아웃)"""
    worker.log.warning(f"Worker timeout - aborting (pid: {worker.pid})")


def worker_exit(server, worker):
    """워커 종료 시"""
    server.log.info(f"Worker exiting (pid: {worker.pid})")

    # 리소스 정리
    # 리소스 정리
    if hasattr(worker, '_redis'):
        try:
            worker._redis.stop_listening()
        except Exception as e:
            server.log.error(f"Redis cleanup error: {e}")

    # 리소스 트래커 정리 (모든 버전 호환)
    try:
        import multiprocessing.resource_tracker as rt

        # Python 3.10 이하 방식
        if hasattr(rt, '_resource_tracker'):
            if hasattr(rt._resource_tracker, '_fd'):
                rt._resource_tracker._fd = None
                server.log.debug("Resource tracker cleaned (old style)")

        # Python 3.11+ 방식 (필요 시)
        # 실제로는 자동 정리되므로 보통 불필요, 실제 필요한 리소스만 정리
        else:
            pass
            # if hasattr(worker, '_redis'):
            #     try:
            #         worker._redis.stop_listening()
            #         server.log.debug("Redis connection closed")
            #     except Exception as e:
            #         server.log.error(f"Redis cleanup error: {e}")
            #
            # if hasattr(worker, '_db_pool'):
            #     try:
            #         worker._db_pool.close_all()
            #         server.log.debug("DB pool closed")
            #     except Exception as e:
            #         server.log.error(f"DB cleanup error: {e}")

    except (AttributeError, ImportError) as e:
        # 정리 실패해도 괜찮음 - 프로세스 종료 시 OS가 정리
        server.log.debug(f"Resource tracker cleanup skipped: {e}")
    except Exception as e:
        server.log.warning(f"Unexpected error in resource tracker cleanup: {e}")



def on_exit(server):
    """서버 종료 시"""
    server.log.info("Shutting down Gunicorn server")

    # 전역 리소스 정리
    # 예: 공유 메모리, 파일 락 등


# ============ 환경별 설정 오버라이드 ============

# 개발 환경
if os.getenv("ENV", 'dev') == "dev":
    workers = 1
    loglevel = "debug"
    reload = True
    timeout = 0
    accesslog = None  # 개발 시 액세스 로그 끄기
elif os.getenv("ENV") == "staging":
    workers = max(2, default_workers // 2)
    timeout = 0
elif os.getenv("ENV") == "prod":
    workers = default_workers
    preload_app = True  # 메모리 절약
    timeout = 3600


