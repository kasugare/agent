import os
import time
import multiprocessing

workers = 4
worker_class = "uvicorn.workers.UvicornWorker"

def on_starting(server):
    print(f"\n{'='*60}")
    print(f"[on_starting] PID={os.getpid()}, Time={time.time():.2f}")
    print(f"             Running in MASTER process")
    print(f"{'='*60}\n")
    time.sleep(1)

def when_ready(server):
    print(f"\n{'='*60}")
    print(f"[when_ready] PID={os.getpid()}, Time={time.time():.2f}")
    print(f"            Socket bound, ready to fork workers")
    print(f"{'='*60}\n")
    time.sleep(1)

def pre_fork(server, worker):
    print(f"\n{'-'*60}")
    print(f"[pre_fork] PID={os.getpid()} (MASTER), Time={time.time():.2f}")
    print(f"          About to fork worker.age={worker.age}")
    print(f"          worker.pid={worker.pid} (None before fork)")
    print(f"{'-'*60}\n")
    time.sleep(0.5)

def post_fork(server, worker):
    print(f"\n{'-'*60}")
    print(f"[post_fork] PID={os.getpid()} (WORKER), Time={time.time():.2f}")
    print(f"           worker.age={worker.age}")
    print(f"           worker.pid={worker.pid} (My PID)")
    print(f"           Process name: {multiprocessing.current_process().name}")
    print(f"{'-'*60}\n")
    time.sleep(0.5)

def worker_exit(server, worker):
    print(f"\n{'-'*60}")
    print(f"[worker_exit] PID={os.getpid()}, Time={time.time():.2f}")
    print(f"             Exiting worker.pid={worker.pid}")
    print(f"{'-'*60}\n")

def on_exit(server):
    print(f"\n{'='*60}")
    print(f"[on_exit] PID={os.getpid()}, Time={time.time():.2f}")
    print(f"         MASTER shutting down")
    print(f"{'='*60}\n")