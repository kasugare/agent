
전체 실행 순서 (Worker 4개 기준)


[Phase 1] Gunicorn 시작
  Master Process (PID: 1000) 생성
    ↓
  on_starting(server) 실행
    - 파일 디스크립터 제한 증가
    - 로깅 설정
    - Master 프로세스 이름 설정: 'gunicorn-master'
    ↓
  when_ready(server) 실행
    - 소켓 바인딩 완료
    - Master PID 저장
    - "Server ready" 로그

────────────────────────────────────────────────────────────

[Phase 2] Worker 1 생성
  Master Process (PID: 1000)에서:
    ↓
  pre_fork(server, worker_1) 실행
    - 현재 프로세스: Master (PID: 1000)
    - worker.age = 0
    - worker.pid는 아직 None (fork 전이라 워커 PID 모름)
    - Master의 리소스 정리 작업
    ↓
  fork() 시스템 콜 실행
    - OS가 Master 프로세스를 복제
    - 메모리 공간 복사 (Copy-on-Write)
    - 파일 디스크립터 상속
    ↓
  분기점 (fork 반환값으로 분기)
    ├─ Master Process (PID: 1000)
    │   - fork() 반환값: 자식 PID (1001)
    │   - 계속 다음 워커 생성 준비
    │
    └─ Worker 1 Process (PID: 1001) ← 새로 생성됨!
        - fork() 반환값: 0
        - Master의 메모리 복사본 가지고 시작
        ↓
      post_fork(server, worker_1) 실행
        - 현재 프로세스: Worker 1 (PID: 1001)
        - worker.pid = 1001
        - worker.age = 0
        - 프로세스 이름 변경: 'gunicorn-worker-0'
        - Redis Connector 생성 (독립적)
        - DB Pool 초기화 (독립적)
        ↓
      FastAPI 앱 초기화
        - uvicorn.workers.UvicornWorker 실행
        ↓
      FastAPI lifespan startup
        - 앱 레벨 리소스 초기화
        - 이벤트 루프 시작
        ↓
      Worker 1 Ready! (요청 받을 준비 완료)

────────────────────────────────────────────────────────────

[Phase 3] Worker 2 생성
  Master Process (PID: 1000)에서:
    ↓
  pre_fork(server, worker_2) 실행
    - 현재 프로세스: Master (PID: 1000)
    - worker.age = 1
    ↓
  fork() 시스템 콜
    ↓
  분기점
    ├─ Master Process (PID: 1000)
    │   - 계속 다음 워커 준비
    │
    └─ Worker 2 Process (PID: 1002)
        ↓
      post_fork(server, worker_2)
        - 현재 프로세스: Worker 2 (PID: 1002)
        - worker.age = 1
        - 프로세스 이름: 'gunicorn-worker-1'
        - Redis Connector 생성 (Worker 1과 독립적)
        ↓
      FastAPI lifespan startup
        ↓
      Worker 2 Ready!

────────────────────────────────────────────────────────────

[Phase 4] Worker 3 생성
  (Worker 2와 동일한 과정)
  Worker 3 (PID: 1003, age: 2) 생성 및 초기화

────────────────────────────────────────────────────────────

[Phase 5] Worker 4 생성
  (Worker 3과 동일한 과정)
  Worker 4 (PID: 1004, age: 3) 생성 및 초기화

────────────────────────────────────────────────────────────

[Phase 6] 정상 운영 중
  Master Process (PID: 1000)
    - 워커 감시
    - 시그널 처리
    - 워커 재시작 관리

  Worker 1 (PID: 1001) ─┐
  Worker 2 (PID: 1002)  ├─ 요청 처리 중
  Worker 3 (PID: 1003)  │
  Worker 4 (PID: 1004) ─┘

────────────────────────────────────────────────────────────

[Phase 7] 종료 과정 (SIGTERM 받음)
  Master Process가 SIGTERM 받음
    ↓
  Master가 모든 워커에게 SIGTERM 전송
    ↓
  각 Worker에서 (병렬로):
    ├─ Worker 1: FastAPI lifespan shutdown
    │             → worker_exit(server, worker_1)
    │             → 프로세스 종료
    │
    ├─ Worker 2: FastAPI lifespan shutdown
    │             → worker_exit(server, worker_2)
    │             → 프로세스 종료
    │
    ├─ Worker 3: (동일)
    │
    └─ Worker 4: (동일)
    ↓
  모든 워커 종료 확인
    ↓
  Master: on_exit(server) 실행
    - 최종 정리 작업
    ↓
  Master Process 종료



────────────────────────────────────────────────────────────



# Gunicorn 시작
$ gunicorn -c gunicorn_conf.py main:app

# 타임스탬프와 함께 실제 로그
[2024-04-08 10:00:00] [1000] [INFO] Starting gunicorn 21.2.0
[2024-04-08 10:00:00] [1000] [INFO] on_starting called (Master PID: 1000)
[2024-04-08 10:00:00] [1000] [INFO] File descriptor limit: 1024 -> 65536
[2024-04-08 10:00:00] [1000] [INFO] Listening at: http://0.0.0.0:8080 (1000)
[2024-04-08 10:00:00] [1000] [INFO] when_ready called (Master PID: 1000)
[2024-04-08 10:00:00] [1000] [INFO] Using worker: uvicorn.workers.UvicornWorker

# Worker 1 생성
[2024-04-08 10:00:00] [1000] [DEBUG] pre_fork called (Master PID: 1000, worker.age: 0)
[2024-04-08 10:00:00] [1000] [INFO] Booting worker with pid: 1001
[2024-04-08 10:00:00] [1001] [INFO] post_fork called (Worker PID: 1001, age: 0)
[2024-04-08 10:00:00] [1001] [INFO] Worker 1001: Redis connector initialized
[2024-04-08 10:00:01] [1001] [INFO] Started server process [1001]
[2024-04-08 10:00:01] [1001] [INFO] Application startup complete (Worker 1001)

# Worker 2 생성
[2024-04-08 10:00:01] [1000] [DEBUG] pre_fork called (Master PID: 1000, worker.age: 1)
[2024-04-08 10:00:01] [1000] [INFO] Booting worker with pid: 1002
[2024-04-08 10:00:01] [1002] [INFO] post_fork called (Worker PID: 1002, age: 1)
[2024-04-08 10:00:01] [1002] [INFO] Worker 1002: Redis connector initialized
[2024-04-08 10:00:02] [1002] [INFO] Started server process [1002]
[2024-04-08 10:00:02] [1002] [INFO] Application startup complete (Worker 1002)

# Worker 3 생성
[2024-04-08 10:00:02] [1000] [DEBUG] pre_fork called (Master PID: 1000, worker.age: 2)
[2024-04-08 10:00:02] [1000] [INFO] Booting worker with pid: 1003
[2024-04-08 10:00:02] [1003] [INFO] post_fork called (Worker PID: 1003, age: 2)
[2024-04-08 10:00:02] [1003] [INFO] Worker 1003: Redis connector initialized
[2024-04-08 10:00:03] [1003] [INFO] Started server process [1003]
[2024-04-08 10:00:03] [1003] [INFO] Application startup complete (Worker 1003)

# Worker 4 생성
[2024-04-08 10:00:03] [1000] [DEBUG] pre_fork called (Master PID: 1000, worker.age: 3)
[2024-04-08 10:00:03] [1000] [INFO] Booting worker with pid: 1004
[2024-04-08 10:00:03] [1004] [INFO] post_fork called (Worker PID: 1004, age: 3)
[2024-04-08 10:00:03] [1004] [INFO] Worker 1004: Redis connector initialized
[2024-04-08 10:00:04] [1004] [INFO] Started server process [1004]
[2024-04-08 10:00:04] [1004] [INFO] Application startup complete (Worker 1004)

# 모든 워커 준비 완료
[2024-04-08 10:00:04] [1000] [INFO] All workers ready. Server started.


===========================================================================================


FastAPI Lifespan과의 통합
중요: FastAPI의 lifespan과 Gunicorn의 후크는 다른 시점에 실행 됨

FastAPI lifespan 사용을 더 권장하는 이유:

Gunicorn에 종속되지 않음 (Uvicorn 단독 실행 가능)
코드가 더 명확하고 유지보수 쉬움
비동기 초기화에 더 적합

-------------------------------------------------------------------
# main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

# Gunicorn post_fork에서 생성한 Redis를 여기서 접근 가능하게
redis_connector = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 앱 시작/종료 시"""
    global redis_connector

    logger = logging.getLogger(__name__)

    # ⚠️ 주의: Gunicorn post_fork에서 이미 생성했다면 재사용
    # 그렇지 않으면 여기서 생성
    if redis_connector is None:
        from common.redis_connector import AsyncRedisConnector
        redis_connector = AsyncRedisConnector(
            logger,
            db=0,
            reload=True,
            isolate_pubsub=True
        )
        logger.info("Redis initialized in FastAPI lifespan")

    # Pub/Sub 구독 시작
    if redis_connector.is_reload_enabled():
        async def on_meta_update(data):
            logger.info(f"Meta updated: {data}")

        await redis_connector.subscribe_async("metadata:update", on_meta_update)

    yield

    # 종료 시
    if redis_connector.is_reload_enabled():
        await redis_connector.stop_listening_async()

    logger.info("FastAPI lifespan cleanup completed")


app = FastAPI(lifespan=lifespan)

-------------------------------------------------------------------


```

## 실행 순서 정리
```
1. on_starting()        # Master에서 1번
   ↓
2. pre_fork()           # Master에서 Worker 수만큼 (4번)
   ↓
3. fork()               # OS 시스템 콜
   ↓
4. post_fork()          # 각 Worker에서 1번씩 (4번)
   ↓
5. FastAPI lifespan()   # 각 Worker에서 1번씩 (4번)
   ↓
   ... 서비스 운영 ...
   ↓
6. FastAPI lifespan 종료  # 각 Worker에서
   ↓
7. worker_exit()        # 각 Worker에서
   ↓
8. on_exit()            # Master에서 1번