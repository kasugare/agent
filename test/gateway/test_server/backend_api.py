"""
Mock Backend API
기존 FastAPI Pod를 시뮬레이션하는 테스트용 API
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import time
import random
from datetime import datetime

app = FastAPI(title="Backend API (Mock)")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "backend-api"}


# ============================================================================
# 사용자 API
# ============================================================================

@app.post("/api/users")
async def create_user(request: Request):
    """사용자 생성"""
    body = await request.json()

    # 처리 시간 시뮬레이션 (1-3초)
    time.sleep(random.uniform(1, 3))

    return {
        "action": "create_user",
        "user_id": f"user_{int(time.time())}",
        "name": body.get("name"),
        "email": body.get("email"),
        "created_at": datetime.now().isoformat(),
        "processing_time": "1-3 seconds"
    }


@app.get("/api/users/{user_id}")
async def get_user(user_id: str):
    """사용자 조회"""
    time.sleep(random.uniform(0.5, 1.5))

    return {
        "action": "get_user",
        "user_id": user_id,
        "name": "John Doe",
        "email": "john@example.com",
        "status": "active"
    }


@app.get("/api/users")
async def list_users():
    """사용자 목록"""
    time.sleep(random.uniform(0.5, 2))

    return {
        "action": "list_users",
        "users": [
            {"id": "user_1", "name": "Alice"},
            {"id": "user_2", "name": "Bob"},
            {"id": "user_3", "name": "Charlie"}
        ],
        "total": 3
    }


@app.put("/api/users/{user_id}")
async def update_user(user_id: str, request: Request):
    """사용자 업데이트"""
    body = await request.json()
    time.sleep(random.uniform(1, 2))

    return {
        "action": "update_user",
        "user_id": user_id,
        "updated_fields": body,
        "message": "User updated successfully"
    }


@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str):
    """사용자 삭제"""
    time.sleep(random.uniform(0.5, 1))

    return {
        "action": "delete_user",
        "user_id": user_id,
        "message": "User deleted successfully"
    }


# ============================================================================
# 주문 API
# ============================================================================

@app.post("/api/orders")
async def create_order(request: Request):
    """주문 생성"""
    body = await request.json()

    # 주문 처리 시뮬레이션 (2-4초)
    time.sleep(random.uniform(2, 4))

    return {
        "action": "create_order",
        "order_id": f"order_{int(time.time())}",
        "user_id": body.get("user_id"),
        "items": body.get("items", []),
        "total_amount": body.get("total_amount", 0),
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "processing_time": "2-4 seconds"
    }


@app.get("/api/orders/{order_id}")
async def get_order(order_id: str):
    """주문 조회"""
    time.sleep(random.uniform(0.5, 1))

    return {
        "action": "get_order",
        "order_id": order_id,
        "status": "completed",
        "total_amount": 59900
    }


@app.get("/api/orders")
async def list_orders():
    """주문 목록"""
    time.sleep(random.uniform(1, 2))

    return {
        "action": "list_orders",
        "orders": [
            {"order_id": "order_1", "status": "pending", "amount": 29900},
            {"order_id": "order_2", "status": "completed", "amount": 49900}
        ],
        "total": 2
    }


# ============================================================================
# 상품 API
# ============================================================================

@app.get("/api/products")
async def list_products():
    """상품 목록"""
    time.sleep(random.uniform(0.5, 1.5))

    return {
        "action": "list_products",
        "products": [
            {"id": "prod_1", "name": "Product A", "price": 29900},
            {"id": "prod_2", "name": "Product B", "price": 39900},
            {"id": "prod_3", "name": "Product C", "price": 49900}
        ],
        "total": 3
    }


@app.get("/api/products/{product_id}")
async def get_product(product_id: str):
    """상품 조회"""
    time.sleep(random.uniform(0.3, 1))

    return {
        "action": "get_product",
        "product_id": product_id,
        "name": "Sample Product",
        "price": 29900,
        "stock": 100
    }


# ============================================================================
# 무거운 처리 API (5-10초)
# ============================================================================

@app.post("/api/process/heavy")
async def heavy_processing(request: Request):
    """무거운 작업 처리"""
    body = await request.json()

    # 무거운 작업 시뮬레이션 (5-10초)
    processing_time = random.uniform(5, 10)
    time.sleep(processing_time)

    return {
        "action": "heavy_processing",
        "type": body.get("type", "default"),
        "processed_items": len(body.get("data", [])),
        "processing_time": f"{processing_time:.2f} seconds",
        "result": "Processing completed successfully"
    }


@app.post("/api/process/batch")
async def batch_processing(request: Request):
    """배치 처리"""
    body = await request.json()

    # 배치 처리 시뮬레이션 (3-6초)
    time.sleep(random.uniform(3, 6))

    return {
        "action": "batch_processing",
        "batch_size": body.get("batch_size", 100),
        "status": "completed",
        "results": {
            "success": 95,
            "failed": 5
        }
    }


# ============================================================================
# ML 추론 API
# ============================================================================

@app.post("/api/ml/inference")
async def ml_inference(request: Request):
    """ML 모델 추론"""
    body = await request.json()

    # ML 추론 시뮬레이션 (2-4초)
    time.sleep(random.uniform(2, 4))

    return {
        "action": "ml_inference",
        "model": body.get("model", "default_model"),
        "prediction": {
            "class": random.choice(["A", "B", "C"]),
            "confidence": round(random.uniform(0.8, 0.99), 2),
            "inference_time": "2-4 seconds"
        }
    }


# ============================================================================
# 타임아웃 테스트용 (60초+ 걸리는 API)
# ============================================================================

@app.post("/api/test/slow")
async def slow_endpoint(request: Request):
    """매우 느린 엔드포인트 (타임아웃 테스트용)"""
    body = await request.json()
    delay = body.get("delay", 65)  # 기본 65초

    print(f"Slow endpoint called, sleeping for {delay} seconds...")
    time.sleep(delay)

    return {
        "action": "slow_processing",
        "delay": delay,
        "message": "Completed after long delay"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8004)
