#!/usr/bin/env python3
"""
Simple Queue System 테스트 스크립트
"""
import requests
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

GATEWAY_URL = "http://localhost:8000"


def test_single_request():
    """단일 요청 테스트 - Long Polling으로 즉시 결과 반환"""
    print("\n" + "=" * 60)
    print("TEST 1: 단일 요청 (Long Polling)")
    print("=" * 60)

    start_time = time.time()

    print("\n사용자 생성 요청...")
    response = requests.post(
        f"{GATEWAY_URL}/api/users",
        json={"name": "Alice", "email": "alice@example.com"},
        timeout=70  # Gateway timeout보다 약간 길게
    )

    elapsed = time.time() - start_time

    print(f"Status Code: {response.status_code}")
    print(f"응답 시간: {elapsed:.2f}초")
    print(f"응답 내용:")
    print(json.dumps(response.json(), indent=2))

    print(f"\n✅ 1번 호출로 결과 받음!")


def test_multiple_requests():
    """동시 다중 요청 테스트 (5개 요청, 3개 Worker)"""
    print("\n" + "=" * 60)
    print("TEST 2: 동시 다중 요청 (5개)")
    print("=" * 60)
    print("예상 동작: 3개는 즉시 처리, 2개는 Queue 대기 후 처리")

    results = []
    start_time = time.time()

    # 5개 요청 동시 전송
    print("\n5개 요청 전송 중...")
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for i in range(10):
            future = executor.submit(
                lambda idx: (
                    idx,
                    time.time(),
                    requests.post(
                        f"{GATEWAY_URL}/api/users",
                        json={"name": f"User{idx + 1}", "email": f"user{idx + 1}@test.com"},
                        timeout=70
                    )
                ),
                i
            )
            futures.append(future)

        for future in as_completed(futures):
            idx, req_start, response = future.result()
            req_elapsed = time.time() - req_start
            results.append((idx, req_elapsed, response))

    total_elapsed = time.time() - start_time

    # 결과 출력
    print(f"\n{'=' * 60}")
    print("처리 결과:")
    results.sort(key=lambda x: x[1])  # 처리 시간 순 정렬

    for idx, elapsed, response in results:
        print(f"  Request {idx + 1}: {elapsed:.2f}초 (Status: {response.status_code})")

    print(f"\n전체 소요 시간: {total_elapsed:.2f}초")
    print(f"✅ 모든 요청 완료!")


def test_different_endpoints():
    """다양한 엔드포인트 테스트"""
    print("\n" + "=" * 60)
    print("TEST 3: 다양한 엔드포인트")
    print("=" * 60)

    tests = [
        ("GET", "/api/users", None),
        ("GET", "/api/users/user_123", None),
        ("POST", "/api/orders", {"user_id": "user_123", "items": [], "total_amount": 10000}),
        ("GET", "/api/products", None),
    ]

    for method, path, data in tests:
        print(f"\n{method} {path}")
        start = time.time()

        try:
            if method == "GET":
                response = requests.get(f"{GATEWAY_URL}{path}", timeout=70)
            else:
                response = requests.post(f"{GATEWAY_URL}{path}", json=data, timeout=70)

            elapsed = time.time() - start

            print(f"  Status: {response.status_code}")
            print(f"  Time: {elapsed:.2f}s")
            print(f"  Response: {json.dumps(response.json(), indent=4)}")

        except Exception as e:
            print(f"  ❌ Error: {e}")


def test_heavy_processing():
    """무거운 작업 테스트 (5-10초 소요)"""
    print("\n" + "=" * 60)
    print("TEST 4: 무거운 작업 (5-10초)")
    print("=" * 60)

    print("\n무거운 처리 요청 전송...")
    start = time.time()

    response = requests.post(
        f"{GATEWAY_URL}/api/process/heavy",
        json={"type": "batch_analysis", "data": list(range(100))},
        timeout=70
    )

    elapsed = time.time() - start

    print(f"Status: {response.status_code}")
    print(f"처리 시간: {elapsed:.2f}초")
    print(f"응답:")
    print(json.dumps(response.json(), indent=2))


def test_timeout():
    """타임아웃 테스트 (60초+ 요청)"""
    print("\n" + "=" * 60)
    print("TEST 5: 타임아웃 테스트 (65초 요청)")
    print("=" * 60)
    print("예상: Gateway에서 60초 후 timeout 응답")

    print("\n65초 소요되는 요청 전송...")
    start = time.time()

    try:
        response = requests.post(
            f"{GATEWAY_URL}/api/test/slow",
            json={"delay": 5},
            timeout=70
        )

        elapsed = time.time() - start

        print(f"Status: {response.status_code}")
        print(f"경과 시간: {elapsed:.2f}초")
        print(f"응답:")
        print(json.dumps(response.json(), indent=2))

        if response.status_code == 504:
            print(f"\n✅ 예상대로 타임아웃 발생!")

    except requests.exceptions.Timeout:
        elapsed = time.time() - start
        print(f"❌ Client timeout 발생 ({elapsed:.2f}초)")


def check_queue_status():
    """Queue 상태 확인"""
    print("\n" + "=" * 60)
    print("Queue 상태 확인")
    print("=" * 60)

    response = requests.get(f"{GATEWAY_URL}/_gateway/queue/status")
    status = response.json()

    print(json.dumps(status, indent=2))
"""
    BACKEND_API_URLS = os.getenv('BACKEND_API_URLS',
                                  'http://127.0.0.1:8001,http://127.0.0.1:8002,http://127.0.0.1:8003').split(',')
"""
def check_metrics():
    """메트릭 확인"""
    print("\n" + "=" * 60)
    print("메트릭 확인")
    print("=" * 60)

    response = requests.get(f"{GATEWAY_URL}/_gateway/metrics")
    metrics = response.json()

    print(json.dumps(metrics, indent=2))


def main():
    """모든 테스트 실행"""
    print("\n" + "=" * 60)
    print("Simple Queue System 테스트")
    print("=" * 60)

    try:
        # Gateway 연결 확인
        print("\nGateway 연결 확인...")
        response = requests.get(f"{GATEWAY_URL}/_gateway/health", timeout=600)
        print(f"✓ Gateway 연결 성공")
        print(f"  {json.dumps(response.json(), indent=2)}")

        # 테스트 실행
        test_single_request()
        time.sleep(0.1)

        test_multiple_requests()
        time.sleep(0.1)

        check_queue_status()
        time.sleep(0.1)

        test_different_endpoints()
        time.sleep(0.1)

        test_heavy_processing()
        time.sleep(0.1)

        test_timeout()
        time.sleep(0.1)

        check_metrics()

        print("\n" + "=" * 60)
        print("✅ 모든 테스트 완료!")
        print("=" * 60 + "\n")

    except requests.exceptions.ConnectionError:
        print(f"\n❌ Gateway에 연결할 수 없습니다: {GATEWAY_URL}")
        print("docker-compose up 명령으로 시스템을 실행하세요.")
    except Exception as e:
        print(f"\n❌ 테스트 실패: {str(e)}")


if __name__ == "__main__":
    main()
