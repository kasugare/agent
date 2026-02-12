"""
Simple Queue Gateway - OOP Architecture
"""
import asyncio
import httpx
import uuid
import threading
import time
import os
from queue import Queue, Empty
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel


# ============================================================================
# Configuration
# ============================================================================

class Config:
    """시스템 설정"""
    # Timeout 설정
    LONG_POLLING_TIMEOUT = 60
    BACKEND_REQUEST_TIMEOUT = 55

    # 백엔드 API 설정
    BACKEND_API_URLS = os.getenv('BACKEND_API_URLS',
                                 'http://127.0.0.1:10005').split(',')

    # 결과 저장 시간
    RESULT_RETENTION_SECONDS = 3600


# ============================================================================
# Data Models
# ============================================================================

class JobRequest(BaseModel):
    """Job 요청 데이터"""
    method: str
    path: str
    headers: Dict[str, str]
    query_params: str
    body: str
    client_host: Optional[str] = None


class JobResult(BaseModel):
    """Job 결과 데이터"""
    job_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
    worker_id: Optional[str] = None
    processing_time: Optional[float] = None
    created_at: str
    completed_at: Optional[str] = None


class BackendAddRequest(BaseModel):
    """Backend 추가 요청"""
    urls: List[str]

    class Config:
        json_schema_extra = {
            "examples": [
                {"urls": ["http://backend-api-4:8001"]},
                {"urls": ["http://backend-api-4:8001", "http://backend-api-5:8001"]}
            ]
        }


class BackendRemoveRequest(BaseModel):
    """Backend 제거 요청"""
    urls: List[str]

    class Config:
        json_schema_extra = {
            "examples": [
                {"urls": ["http://backend-api-4:8001"]},
                {"urls": ["http://backend-api-4:8001", "http://backend-api-5:8001"]}
            ]
        }


class BackendDrainRequest(BaseModel):
    """Backend Drain 요청"""
    urls: List[str]

    class Config:
        json_schema_extra = {
            "examples": [
                {"urls": ["http://backend-api-4:8001"]},
                {"urls": ["http://backend-api-4:8001", "http://backend-api-5:8001"]}
            ]
        }


# ============================================================================
# Job Queue Manager
# ============================================================================

class JobQueueManager:
    """
    In-Memory Job Queue 관리자
    """

    def __init__(self):
        self.job_queue = Queue()
        self.results: Dict[str, JobResult] = {}
        self.results_lock = threading.Lock()

        self.stats = {
            'total_jobs': 0,
            'completed_jobs': 0,
            'failed_jobs': 0,
            'timeout_jobs': 0
        }
        self.stats_lock = threading.Lock()

    def submit_job(self, job_id: str, job_data: JobRequest) -> None:
        """Job을 Queue에 추가"""
        result = JobResult(
            job_id=job_id,
            status='queued',
            created_at=datetime.now().isoformat()
        )

        with self.results_lock:
            self.results[job_id] = result

        self.job_queue.put((job_id, job_data))

        with self.stats_lock:
            self.stats['total_jobs'] += 1

        print(f"[QueueManager] Job {job_id[:8]} queued (Queue size: {self.job_queue.qsize()})")

    def get_job(self, timeout: float = 1.0) -> Optional[tuple]:
        """Queue에서 Job 가져오기"""
        try:
            return self.job_queue.get(timeout=timeout)
        except Empty:
            return None

    def update_result(self, job_id: str, status: str, result: Any = None,
                     error: str = None, worker_id: str = None,
                     processing_time: float = None) -> None:
        """Job 결과 업데이트"""
        with self.results_lock:
            if job_id in self.results:
                self.results[job_id].status = status
                self.results[job_id].result = result
                self.results[job_id].error = error
                self.results[job_id].worker_id = worker_id
                self.results[job_id].processing_time = processing_time
                self.results[job_id].completed_at = datetime.now().isoformat()

        with self.stats_lock:
            if status == 'success':
                self.stats['completed_jobs'] += 1
            elif status == 'failed':
                self.stats['failed_jobs'] += 1
            elif status == 'timeout':
                self.stats['timeout_jobs'] += 1

    def get_result(self, job_id: str) -> Optional[JobResult]:
        """Job 결과 조회"""
        with self.results_lock:
            return self.results.get(job_id)

    def wait_for_result(self, job_id: str, timeout: float) -> Optional[JobResult]:
        """Job 결과가 나올 때까지 대기 (Long Polling)"""
        start_time = time.time()

        while True:
            result = self.get_result(job_id)

            if result and result.status in ['success', 'failed', 'timeout']:
                return result

            if time.time() - start_time >= timeout:
                self.update_result(job_id, 'timeout',
                                  error=f'Request timeout after {timeout} seconds')
                return self.get_result(job_id)

            time.sleep(0.1)

    def get_queue_status(self) -> Dict[str, Any]:
        """Queue 상태 정보 반환"""
        with self.results_lock:
            processing_count = sum(1 for r in self.results.values() if r.status == 'processing')
            queued_count = self.job_queue.qsize()

        with self.stats_lock:
            stats = self.stats.copy()

        return {
            'queue_size': queued_count,
            'processing': processing_count,
            'statistics': stats
        }

    def cleanup_old_results(self, max_age_seconds: int = 3600):
        """오래된 결과 정리"""
        with self.results_lock:
            current_time = datetime.now()
            to_delete = []

            for job_id, result in self.results.items():
                if result.completed_at:
                    completed_time = datetime.fromisoformat(result.completed_at)
                    age = (current_time - completed_time).total_seconds()

                    if age > max_age_seconds:
                        to_delete.append(job_id)

            for job_id in to_delete:
                del self.results[job_id]

            if to_delete:
                print(f"[QueueManager] Cleaned up {len(to_delete)} old results")


# ============================================================================
# Backend Pod Manager
# ============================================================================

class BackendPodManager:
    """
    Backend Pod 상태 추적 및 관리
    """

    def __init__(self, backend_urls: List[str]):
        self.pods = {}
        self.lock = threading.Lock()

        for url in backend_urls:
            self.pods[url] = {
                'busy': False,
                'current_job_id': None,
                'total_processed': 0,
                'last_used': None,
                'draining': False
            }

        print(f"[BackendPodManager] Initialized with {len(self.pods)} backend pods:")
        for url in self.pods.keys():
            print(f"  - {url}")

    def add_backend(self, url: str) -> bool:
        """Backend Pod 추가"""
        with self.lock:
            if url in self.pods:
                return False

            self.pods[url] = {
                'busy': False,
                'current_job_id': None,
                'total_processed': 0,
                'last_used': None,
                'draining': False
            }

            print(f"[BackendPodManager] Added backend: {url}")
            return True

    def remove_backend(self, url: str) -> bool:
        """Backend Pod 제거 (drain 모드이고 busy가 아닐 때만)"""
        with self.lock:
            if url not in self.pods:
                return False

            if not self.pods[url]['draining']:
                return False

            if self.pods[url]['busy']:
                return False

            del self.pods[url]
            print(f"[BackendPodManager] Removed backend: {url}")
            return True

    def start_draining(self, url: str) -> bool:
        """Backend를 drain 모드로 설정"""
        with self.lock:
            if url not in self.pods:
                return False

            self.pods[url]['draining'] = True
            print(f"[BackendPodManager] Started draining: {url}")
            return True

    def stop_draining(self, url: str) -> bool:
        """Backend의 drain 모드 해제"""
        with self.lock:
            if url not in self.pods:
                return False

            self.pods[url]['draining'] = False
            print(f"[BackendPodManager] Stopped draining: {url}")
            return True

    def get_available_pod(self) -> Optional[str]:
        """유휴한 Pod URL 반환 (drain 모드가 아닌 것만)"""
        with self.lock:
            for url, status in self.pods.items():
                if not status['busy'] and not status['draining']:
                    return url
        return None

    def mark_busy(self, url: str, job_id: str) -> bool:
        """Pod를 busy 상태로 마킹"""
        with self.lock:
            if url in self.pods and not self.pods[url]['busy']:
                self.pods[url]['busy'] = True
                self.pods[url]['current_job_id'] = job_id
                self.pods[url]['last_used'] = datetime.now()
                return True
        return False

    def mark_free(self, url: str):
        """Pod를 free 상태로 마킹"""
        with self.lock:
            if url in self.pods:
                self.pods[url]['busy'] = False
                self.pods[url]['current_job_id'] = None
                self.pods[url]['total_processed'] += 1

    def get_status(self) -> Dict[str, Any]:
        """모든 Pod의 상태 반환"""
        with self.lock:
            return {
                url: {
                    'busy': status['busy'],
                    'current_job_id': status['current_job_id'],
                    'total_processed': status['total_processed'],
                    'last_used': status['last_used'].isoformat() if status['last_used'] else None,
                    'draining': status['draining']
                }
                for url, status in self.pods.items()
            }

    def get_available_count(self) -> int:
        """유휴한 Pod 개수"""
        with self.lock:
            return sum(1 for status in self.pods.values()
                      if not status['busy'] and not status['draining'])

    def get_draining_backends(self) -> List[str]:
        """drain 모드인 Backend 목록"""
        with self.lock:
            return [url for url, status in self.pods.items() if status['draining']]

    def get_backend_list(self) -> List[str]:
        """등록된 모든 Backend URL 목록"""
        with self.lock:
            return list(self.pods.keys())


# ============================================================================
# Worker
# ============================================================================

class Worker:
    """
    Queue의 Job을 처리하는 Worker
    """

    def __init__(self, worker_id: int, queue_manager: JobQueueManager, backend_manager: BackendPodManager):
        self.worker_id = worker_id
        self.queue_manager = queue_manager
        self.backend_manager = backend_manager
        self.is_running = False
        self.thread = None

    def start(self):
        """Worker 시작"""
        self.is_running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print(f"[Worker-{self.worker_id}] Started")

    def stop(self):
        """Worker 중지"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        print(f"[Worker-{self.worker_id}] Stopped")

    def _run(self):
        """Worker 메인 루프"""
        while self.is_running:
            job_item = self.queue_manager.get_job(timeout=1.0)

            if job_item is None:
                continue

            job_id, job_data = job_item

            backend_url = self._wait_for_available_backend()

            if backend_url is None:
                print(f"[Worker-{self.worker_id}] No available backend for job {job_id[:8]}")
                self.queue_manager.update_result(
                    job_id, 'failed',
                    error='No available backend pod',
                    worker_id=f"worker-{self.worker_id}"
                )
                continue

            try:
                self._process_job(job_id, job_data, backend_url)
            except Exception as e:
                print(f"[Worker-{self.worker_id}] Error processing job {job_id[:8]}: {e}")
                self.queue_manager.update_result(
                    job_id, 'failed',
                    error=str(e),
                    worker_id=f"worker-{self.worker_id}"
                )
            finally:
                self.backend_manager.mark_free(backend_url)

    def _wait_for_available_backend(self, timeout: float = 300) -> Optional[str]:
        """유휴한 Backend Pod가 나타날 때까지 대기"""
        start_time = time.time()

        while self.is_running:
            backend_url = self.backend_manager.get_available_pod()

            if backend_url:
                return backend_url

            if time.time() - start_time > timeout:
                return None

            time.sleep(0.1)

        return None

    def _process_job(self, job_id: str, job_data: JobRequest, backend_url: str):
        """실제 Job 처리"""
        start_time = time.time()

        print(f"[Worker-{self.worker_id}] Processing job {job_id[:8]} - {job_data.method} {job_data.path}")
        print(f"[Worker-{self.worker_id}]   → Backend: {backend_url}")

        if not self.backend_manager.mark_busy(backend_url, job_id):
            raise Exception(f"Failed to mark backend {backend_url} as busy")

        self.queue_manager.update_result(
            job_id, 'processing',
            worker_id=f"worker-{self.worker_id}"
        )

        try:
            full_url = f"{backend_url}{job_data.path}"
            if job_data.query_params:
                full_url += f"?{job_data.query_params}"

            headers = {k: v for k, v in job_data.headers.items()
                      if k.lower() not in ['host', 'content-length']}

            with httpx.Client(timeout=Config.BACKEND_REQUEST_TIMEOUT) as client:
                response = client.request(
                    method=job_data.method,
                    url=full_url,
                    headers=headers,
                    content=job_data.body.encode('utf-8') if job_data.body else None
                )

            processing_time = time.time() - start_time

            result_data = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'body': response.text,
                'backend_url': backend_url
            }

            try:
                result_data['json'] = response.json()
            except:
                pass

            self.queue_manager.update_result(
                job_id, 'success',
                result=result_data,
                worker_id=f"worker-{self.worker_id}",
                processing_time=processing_time
            )

            print(f"[Worker-{self.worker_id}] Completed job {job_id[:8]} in {processing_time:.2f}s")

        except httpx.TimeoutException:
            processing_time = time.time() - start_time
            self.queue_manager.update_result(
                job_id, 'failed',
                error='Backend API timeout',
                worker_id=f"worker-{self.worker_id}",
                processing_time=processing_time
            )
            print(f"[Worker-{self.worker_id}] Job {job_id[:8]} timed out")

        except Exception as e:
            processing_time = time.time() - start_time
            self.queue_manager.update_result(
                job_id, 'failed',
                error=str(e),
                worker_id=f"worker-{self.worker_id}",
                processing_time=processing_time
            )
            print(f"[Worker-{self.worker_id}] Job {job_id[:8]} failed: {e}")


# ============================================================================
# Worker Manager
# ============================================================================

class WorkerManager:
    """
    Worker 동적 관리
    """

    def __init__(self):
        self.workers: List[Worker] = []
        self.next_worker_id = 1
        self.lock = threading.Lock()

    def add_worker(self, queue_manager: JobQueueManager, backend_manager: BackendPodManager) -> int:
        """Worker 추가"""
        with self.lock:
            worker = Worker(self.next_worker_id, queue_manager, backend_manager)
            worker.start()
            self.workers.append(worker)

            worker_id = self.next_worker_id
            self.next_worker_id += 1

            print(f"[WorkerManager] Added Worker-{worker_id} (Total: {len(self.workers)})")
            return worker_id

    def remove_worker(self) -> bool:
        """Worker 제거"""
        with self.lock:
            if len(self.workers) == 0:
                return False

            worker = self.workers.pop()
            worker.stop()

            print(f"[WorkerManager] Removed Worker-{worker.worker_id} (Total: {len(self.workers)})")
            return True

    def get_worker_count(self) -> int:
        """현재 Worker 수"""
        with self.lock:
            return len(self.workers)

    def stop_all(self):
        """모든 Worker 종료"""
        with self.lock:
            for worker in self.workers:
                worker.stop()
            self.workers.clear()
            print(f"[WorkerManager] Stopped all workers")

    def restart_all(self, queue_manager: JobQueueManager, backend_manager: BackendPodManager, target_count: int):
        """모든 Worker 재시작"""
        self.stop_all()

        with self.lock:
            self.next_worker_id = 1
            for i in range(target_count):
                worker = Worker(self.next_worker_id, queue_manager, backend_manager)
                worker.start()
                self.workers.append(worker)
                self.next_worker_id += 1

        print(f"[WorkerManager] Restarted {target_count} workers")


# ============================================================================
# Gateway Application
# ============================================================================

class GatewayApplication:
    """
    Gateway 애플리케이션 메인 클래스
    """

    def __init__(self):
        self.queue_manager = JobQueueManager()
        self.backend_manager: Optional[BackendPodManager] = None
        self.worker_manager = WorkerManager()
        self.app = FastAPI(
            title="Simple Queue Gateway",
            description="OOP-based In-Memory Queue with Long Polling",
            version="2.0.0",
            lifespan=self._lifespan
        )

        self._setup_routes()

    @asynccontextmanager
    async def _lifespan(self, app: FastAPI):
        """애플리케이션 라이프사이클 관리"""
        print(f"\n{'='*60}")
        print(f"Starting Simple Queue Gateway (OOP)")
        print(f"{'='*60}")
        print(f"Backend Pods: {len(Config.BACKEND_API_URLS)}")
        for i, url in enumerate(Config.BACKEND_API_URLS, 1):
            print(f"  {i}. {url}")
        print(f"{'='*60}\n")

        # Backend Manager 초기화
        self.backend_manager = BackendPodManager(Config.BACKEND_API_URLS)

        # Workers 시작
        initial_worker_count = len(self.backend_manager.get_backend_list())
        print(f"Starting {initial_worker_count} workers (1 per backend)...")

        for i in range(initial_worker_count):
            self.worker_manager.add_worker(self.queue_manager, self.backend_manager)

        print(f"{'='*60}\n")

        # Cleanup 스레드
        cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        cleanup_thread.start()

        yield

        print("\nStopping all workers...")
        self.worker_manager.stop_all()

    def _cleanup_loop(self):
        """주기적 정리 작업"""
        while True:
            time.sleep(600)
            self.queue_manager.cleanup_old_results(Config.RESULT_RETENTION_SECONDS)

    def _setup_routes(self):
        """라우트 설정"""

        # Gateway 관리 API
        @self.app.get("/_gateway/health")
        async def health_check():
            return self._handle_health_check()

        @self.app.get("/_gateway/queue/status")
        async def queue_status():
            return self._handle_queue_status()

        @self.app.get("/_gateway/metrics")
        async def metrics():
            return self._handle_metrics()

        @self.app.post("/_gateway/reset")
        async def reset_workers():
            return self._handle_reset()

        # Backend 관리 API
        @self.app.post("/_gateway/backends/add")
        async def add_backend(request: BackendAddRequest):
            return self._handle_add_backend(request)

        @self.app.post("/_gateway/backends/remove")
        async def remove_backend(request: BackendRemoveRequest):
            return self._handle_remove_backend(request)

        @self.app.post("/_gateway/backends/drain")
        async def drain_backends(request: BackendDrainRequest):
            return self._handle_drain_backends(request)

        @self.app.post("/_gateway/backends/undrain")
        async def undrain_backends(request: BackendDrainRequest):
            return self._handle_undrain_backends(request)

        @self.app.get("/_gateway/backends/list")
        async def list_backends():
            return self._handle_list_backends()

        # Catch-all 라우트
        @self.app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
        async def gateway_endpoint(request: Request, full_path: str):
            return await self._handle_gateway_request(request, full_path)

    # Handler Methods
    def _handle_health_check(self):
        """헬스 체크"""
        status = self.queue_manager.get_queue_status()

        return {
            'status': 'healthy',
            'service': 'simple-queue-gateway',
            'workers': self.worker_manager.get_worker_count(),
            'backends': len(self.backend_manager.get_backend_list()),
            'queue_status': status
        }

    def _handle_queue_status(self):
        """Queue 상태"""
        return self.queue_manager.get_queue_status()

    def _handle_metrics(self):
        """메트릭"""
        status = self.queue_manager.get_queue_status()
        backend_status = self.backend_manager.get_status()
        available_backends = self.backend_manager.get_available_count()
        current_workers = self.worker_manager.get_worker_count()
        total_backends = len(self.backend_manager.get_backend_list())

        return {
            'workers': {
                'total': current_workers,
                'target': total_backends
            },
            'queue': {
                'pending': status['queue_size'],
                'processing': status['processing']
            },
            'backend_servers': {
                'total': total_backends,
                'available': available_backends,
                'busy': total_backends - available_backends,
                'details': backend_status
            },
            'statistics': status['statistics'],
            'config': {
                'long_polling_timeout': Config.LONG_POLLING_TIMEOUT,
                'backend_api_urls': self.backend_manager.get_backend_list()
            }
        }

    def _handle_reset(self):
        """Worker 리셋"""
        print("\n" + "="*60)
        print("RESET: Resetting all workers...")
        print("="*60)

        for url in self.backend_manager.get_backend_list():
            self.backend_manager.mark_free(url)

        print("Backend pods reset to free state")

        target_worker_count = len(self.backend_manager.get_backend_list())
        self.worker_manager.restart_all(self.queue_manager, self.backend_manager, target_worker_count)

        print("="*60)
        print("RESET: Complete")
        print("="*60 + "\n")

        return {
            'status': 'success',
            'message': 'All workers have been reset',
            'workers_restarted': target_worker_count,
            'backend_servers_reset': len(self.backend_manager.get_backend_list()),
            'timestamp': datetime.now().isoformat()
        }

    def _handle_add_backend(self, request: BackendAddRequest):
        """Backend 추가"""
        urls = request.urls

        if not urls:
            return JSONResponse(
                status_code=400,
                content={'status': 'error', 'message': 'URLs list cannot be empty'}
            )

        results = []
        added_count = 0
        worker_ids = []
        errors = []

        for url in urls:
            if not url.startswith('http://') and not url.startswith('https://'):
                errors.append({'url': url, 'error': 'URL must start with http:// or https://'})
                continue

            success = self.backend_manager.add_backend(url)

            if success:
                worker_id = self.worker_manager.add_worker(self.queue_manager, self.backend_manager)
                results.append({'url': url, 'status': 'added', 'worker_id': worker_id})
                added_count += 1
                worker_ids.append(worker_id)
            else:
                errors.append({'url': url, 'error': 'Backend already exists'})

        response_data = {
            'status': 'success' if added_count > 0 else 'error',
            'message': f'Added {added_count} backend(s) and worker(s)',
            'added_count': added_count,
            'total_backends': len(self.backend_manager.get_backend_list()),
            'total_workers': self.worker_manager.get_worker_count(),
            'results': results,
            'timestamp': datetime.now().isoformat()
        }

        if errors:
            response_data['errors'] = errors

        if added_count == 0:
            return JSONResponse(status_code=400, content=response_data)

        return response_data

    def _handle_remove_backend(self, request: BackendRemoveRequest):
        """Backend 제거"""
        urls = request.urls

        if not urls:
            return JSONResponse(
                status_code=400,
                content={'status': 'error', 'message': 'URLs list cannot be empty'}
            )

        results = []
        removed_count = 0
        errors = []
        backend_status = self.backend_manager.get_status()

        for url in urls:
            success = self.backend_manager.remove_backend(url)

            if success:
                worker_removed = self.worker_manager.remove_worker()
                results.append({'url': url, 'status': 'removed', 'worker_removed': worker_removed})
                removed_count += 1
            else:
                if url not in backend_status:
                    errors.append({'url': url, 'error': 'Backend not found', 'code': 'not_found'})
                elif not backend_status[url]['draining']:
                    errors.append({
                        'url': url,
                        'error': 'Backend must be drained first',
                        'code': 'not_drained',
                        'hint': f'POST /_gateway/backends/drain with {{"urls": ["{url}"]}}'
                    })
                elif backend_status[url]['busy']:
                    errors.append({
                        'url': url,
                        'error': 'Cannot remove busy backend',
                        'code': 'busy',
                        'current_job_id': backend_status[url]['current_job_id'],
                        'hint': 'Wait for the job to complete'
                    })
                else:
                    errors.append({'url': url, 'error': 'Failed to remove backend', 'code': 'unknown'})

        response_data = {
            'status': 'success' if removed_count > 0 else 'error',
            'message': f'Removed {removed_count} backend(s) and worker(s)',
            'removed_count': removed_count,
            'total_backends': len(self.backend_manager.get_backend_list()),
            'total_workers': self.worker_manager.get_worker_count(),
            'results': results,
            'timestamp': datetime.now().isoformat()
        }

        if errors:
            response_data['errors'] = errors

        if removed_count == 0:
            if any(e.get('code') == 'not_drained' for e in errors):
                return JSONResponse(status_code=400, content=response_data)
            elif any(e.get('code') == 'busy' for e in errors):
                return JSONResponse(status_code=409, content=response_data)
            elif all(e.get('code') == 'not_found' for e in errors):
                return JSONResponse(status_code=404, content=response_data)
            else:
                return JSONResponse(status_code=400, content=response_data)

        return response_data

    def _handle_drain_backends(self, request: BackendDrainRequest):
        """Backend Drain"""
        urls = request.urls

        if not urls:
            return JSONResponse(
                status_code=400,
                content={'status': 'error', 'message': 'URLs list cannot be empty'}
            )

        results = []
        drained_count = 0
        errors = []

        for url in urls:
            success = self.backend_manager.start_draining(url)

            if success:
                backend_status = self.backend_manager.get_status()
                is_busy = backend_status[url]['busy']

                results.append({
                    'url': url,
                    'status': 'draining',
                    'currently_busy': is_busy,
                    'message': 'Processing current job...' if is_busy else 'Ready to be removed'
                })
                drained_count += 1
            else:
                errors.append({'url': url, 'error': 'Backend not found'})

        response_data = {
            'status': 'success' if drained_count > 0 else 'error',
            'message': f'Set {drained_count} backend(s) to draining mode',
            'drained_count': drained_count,
            'results': results,
            'hint': 'Use /backends/list to monitor drain status, then /backends/remove when ready',
            'timestamp': datetime.now().isoformat()
        }

        if errors:
            response_data['errors'] = errors

        if drained_count == 0:
            return JSONResponse(status_code=404, content=response_data)

        return response_data

    def _handle_undrain_backends(self, request: BackendDrainRequest):
        """Backend Undrain"""
        urls = request.urls

        if not urls:
            return JSONResponse(
                status_code=400,
                content={'status': 'error', 'message': 'URLs list cannot be empty'}
            )

        results = []
        undrained_count = 0
        errors = []

        for url in urls:
            success = self.backend_manager.stop_draining(url)

            if success:
                results.append({
                    'url': url,
                    'status': 'active',
                    'message': 'Backend is now accepting new jobs'
                })
                undrained_count += 1
            else:
                errors.append({'url': url, 'error': 'Backend not found'})

        response_data = {
            'status': 'success' if undrained_count > 0 else 'error',
            'message': f'Undrained {undrained_count} backend(s)',
            'undrained_count': undrained_count,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }

        if errors:
            response_data['errors'] = errors

        if undrained_count == 0:
            return JSONResponse(status_code=404, content=response_data)

        return response_data

    def _handle_list_backends(self):
        """Backend 목록"""
        backend_status = self.backend_manager.get_status()

        backends = []
        for url, status in backend_status.items():
            backends.append({
                'url': url,
                'busy': status['busy'],
                'draining': status['draining'],
                'current_job_id': status['current_job_id'],
                'total_processed': status['total_processed'],
                'last_used': status['last_used']
            })

        return {
            'total': len(backends),
            'available': self.backend_manager.get_available_count(),
            'busy': sum(1 for b in backends if b['busy']),
            'draining': len(self.backend_manager.get_draining_backends()),
            'backends': backends
        }

    async def _handle_gateway_request(self, request: Request, full_path: str):
        """Gateway 메인 요청 처리"""
        job_id = str(uuid.uuid4())

        try:
            body = await request.body()
            body_str = body.decode('utf-8') if body else ""
        except:
            body_str = ""

        job_data = JobRequest(
            method=request.method,
            path=f"/{full_path}",
            headers={k: v for k, v in request.headers.items()},
            query_params=str(request.query_params) if request.query_params else "",
            body=body_str,
            client_host=request.client.host if request.client else None
        )

        print(f"\n[Gateway] Received {request.method} /{full_path} -> Job {job_id[:8]}")

        self.queue_manager.submit_job(job_id, job_data)

        result = await asyncio.to_thread(
            self.queue_manager.wait_for_result,
            job_id,
            Config.LONG_POLLING_TIMEOUT
        )

        if not result:
            raise HTTPException(status_code=500, detail="Failed to get job result")

        if result.status == 'success':
            backend_response = result.result

            return JSONResponse(
                content=backend_response.get('json') or backend_response.get('body'),
                status_code=backend_response.get('status_code', 200),
                headers={k: v for k, v in backend_response.get('headers', {}).items()
                        if k.lower() not in ['content-encoding', 'content-length', 'transfer-encoding']}
            )

        elif result.status == 'timeout':
            return JSONResponse(
                status_code=504,
                content={
                    'error': 'Gateway Timeout',
                    'message': f'Request processing timeout after {Config.LONG_POLLING_TIMEOUT} seconds',
                    'job_id': job_id
                }
            )

        else:
            return JSONResponse(
                status_code=500,
                content={
                    'error': 'Processing Failed',
                    'message': result.error,
                    'job_id': job_id
                }
            )

    def get_app(self) -> FastAPI:
        """FastAPI 앱 반환"""
        return self.app


# ============================================================================
# Application Entry Point
# ============================================================================

# 애플리케이션 인스턴스 생성
gateway_app = GatewayApplication()
app = gateway_app.get_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8005,
        timeout_keep_alive=Config.LONG_POLLING_TIMEOUT + 10
    )

