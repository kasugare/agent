from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uvicorn
from datetime import datetime
import asyncio
import uuid
import json
import random


# 데이터 모델 정의
class WorkflowStartRequest(BaseModel):
    node_id: str
    input_data: Dict[str, Any]
    request_id: Optional[str] = None

class WorkflowRequest(BaseModel):
    node_id: str
    # input_data: List[Dict[str, Any]]
    input_data: Dict[str, Any]
    request_id: Optional[str] = None

class WorkflowResponse(BaseModel):
    request_id: str
    node_id: str
    status: str
    data: str
    timestamp: str


class WorkflowMergeResponse(BaseModel):
    request_id: str
    node_id: str
    status: str
    data: Dict[str, Any]
    timestamp: str


# Node A (Start Node) - API Gateway
app_node_a = FastAPI(title="Node A - API Gateway")
@app_node_a.post("/workflow/start")#, response_model=WorkflowResponse)
async def start_workflow(request: WorkflowStartRequest):
    print("#" * 100)
    print(f"# Node A - {request.input_data}")
    request_id = request.request_id or str(uuid.uuid4())

    response = {
        "request_id": request_id,
        "node_id": "node_a",
        "status": "success",
        "data": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "timestamp": datetime.now().isoformat()
    }

    return response


# Node B - Business Logic 1
app_node_b = FastAPI(title="Node B - Business Logic 1")
@app_node_b.post("/process", response_model=WorkflowResponse)
async def process_node_b(request: WorkflowRequest):
    print(f"# Node B - {request.input_data}")
    # 비즈니스 로직 시뮬레이션을 위한 지연
    await asyncio.sleep(random.randrange(1, 5)*0.1)

    input_data = request.input_data
    # print(input_data)

    return WorkflowResponse(
        request_id=request.request_id,
        node_id="node_b",
        status="success",
        data="Summary model",
        timestamp=datetime.now().isoformat()
    )


# Node C - Business Logic 2
app_node_c = FastAPI(title="Node C - Business Logic 2")
@app_node_c.post("/process", response_model=WorkflowResponse)
async def process_node_c(request: WorkflowRequest):
    print(f"# Node C - {request.input_data}")
    await asyncio.sleep(random.randrange(1, 5)*0.1)

    input_data = request.input_data
    # print(input_data)

    return WorkflowResponse(
        request_id=request.request_id,
        node_id="node_c",
        status="success",
        data="Classification model",
        timestamp=datetime.now().isoformat()
    )


# Node D - Business Logic 3
app_node_d = FastAPI(title="Node D - Business Logic 3")
@app_node_d.post("/process", response_model=WorkflowResponse)
async def process_node_d(request: WorkflowRequest):
    print(f"# Node D - {request.input_data}")
    await asyncio.sleep(random.randrange(1, 5)*0.1)

    input_data = request.input_data
    # print(input_data)

    return WorkflowResponse(
        request_id=request.request_id,
        node_id="node_d",
        status="success",
        data="Classification model",
        timestamp=datetime.now().isoformat()
    )


# Node E - Business Logic 3
app_node_e = FastAPI(title="Node E - Business Logic 4")
@app_node_e.post("/process", response_model=WorkflowResponse)
async def process_node_d(request: WorkflowRequest):
    print(f"# Node E - {request.input_data}")
    await asyncio.sleep(random.randrange(1, 5)*0.1)

    input_data = request.input_data
    # print(input_data)

    return WorkflowResponse(
        request_id=request.request_id,
        node_id="node_e",
        status="success",
        data="Classification model",
        timestamp=datetime.now().isoformat()
    )


# Node F - Business Logic 3
app_node_f = FastAPI(title="Node F - Business Logic 5")
@app_node_f.post("/process", response_model=WorkflowResponse)
async def process_node_d(request: WorkflowRequest):
    print(f"# Node F - {request.input_data}")
    await asyncio.sleep(random.randrange(1, 5)*0.1)

    input_data = request.input_data
    # print(input_data)

    return WorkflowResponse(
        request_id=request.request_id,
        node_id="node_f",
        status="success",
        data="Classification model",
        timestamp=datetime.now().isoformat()
    )

# Node G - Business Logic 3
app_node_g = FastAPI(title="Node G - Business Logic 6")
@app_node_g.post("/process", response_model=WorkflowResponse)
async def process_node_d(request: WorkflowRequest):
    print(f"# Node G - {request.input_data}")
    await asyncio.sleep(random.randrange(1, 5)*0.1)

    input_data = request.input_data
    # print(input_data)

    return WorkflowResponse(
        request_id=request.request_id,
        node_id="node_g",
        status="success",
        data="Classification model",
        timestamp=datetime.now().isoformat()
    )


# Node H - Business Logic 3
app_node_h = FastAPI(title="Node H - Business Logic 7")
@app_node_h.post("/process", response_model=WorkflowResponse)
async def process_node_d(request: WorkflowRequest):
    print(f"# Node H - {request.input_data}")
    await asyncio.sleep(random.randrange(1, 5)*0.1)

    input_data = request.input_data
    # print(input_data)

    return WorkflowResponse(
        request_id=request.request_id,
        node_id="node_h",
        status="success",
        data="Classification model",
        timestamp=datetime.now().isoformat()
    )


# Node I - Business Logic: aggregate
app_node_i = FastAPI(title="Node I - Business Logic aggregate 1")
@app_node_i.post("/aggregate", response_model=WorkflowMergeResponse)
async def process_node_d(request: WorkflowRequest):
    print(f"# Node I - {request.input_data}")
    await asyncio.sleep(random.randrange(1, 5)*0.1)

    input_data = request.input_data
    # print(input_data)

    processed_data = {
        "result": {
            # "summery": input_data['node_b'],
            # "classification": input_data['node_c']
        }
    }

    return WorkflowMergeResponse(
        request_id=request.request_id,
        node_id="node_i",
        status="success",
        data=processed_data,
        timestamp=datetime.now().isoformat()
    )


# Node J - Business Logic: aggregate
app_node_j = FastAPI(title="Node J - Business Logic aggregate 2")
@app_node_j.post("/aggregate", response_model=WorkflowMergeResponse)
async def process_node_d(request: WorkflowRequest):
    print(f"# Node J - {request.input_data}")
    await asyncio.sleep(random.randrange(1, 5)*0.1)

    input_data = request.input_data
    # print(input_data)

    processed_data = {
        "result": {
            # "summery": input_data['node_b'],
            # "classification": input_data['node_c']
        }
    }

    return WorkflowMergeResponse(
        request_id=request.request_id,
        node_id="node_j",
        status="success",
        data=processed_data,
        timestamp=datetime.now().isoformat()
    )

# Node z - Result Aggregator
app_node_z = FastAPI(title="Node E - Result Aggregator 3")
@app_node_z.post("/aggregate", response_model=WorkflowResponse)
async def aggregate_results(request: WorkflowRequest):
    print(f"# Node H - {request.input_data}")

    input_data = request.input_data

    # 모든 노드의 결과 취합
    aggregated_data = {
        "node_id": request.node_id,
        "request_id": request.request_id,
        "results": input_data,
        "aggregated_at": datetime.now().isoformat()
    }

    return WorkflowResponse(
        request_id=request.request_id,
        node_id="node_e",
        status="success",
        data=aggregated_data,
        timestamp=datetime.now().isoformat()
    )


# 각 노드별 서버 실행을 위한 설정
def run_node_a():
    uvicorn.run(app_node_a, host="127.0.0.1", port=10001)


def run_node_b():
    uvicorn.run(app_node_b, host="127.0.0.1", port=10002)


def run_node_c():
    uvicorn.run(app_node_c, host="127.0.0.1", port=10003)


def run_node_d():
    uvicorn.run(app_node_d, host="127.0.0.1", port=10004)


def run_node_e():
    uvicorn.run(app_node_e, host="127.0.0.1", port=10005)


def run_node_f():
    uvicorn.run(app_node_f, host="127.0.0.1", port=10006)


def run_node_g():
    uvicorn.run(app_node_g, host="127.0.0.1", port=10007)


def run_node_h():
    uvicorn.run(app_node_h, host="127.0.0.1", port=10008)


def run_node_i():
    uvicorn.run(app_node_i, host="127.0.0.1", port=10009)


def run_node_j():
    uvicorn.run(app_node_j, host="127.0.0.1", port=10010)


def run_node_z():
    uvicorn.run(app_node_z, host="127.0.0.1", port=10011)


# 테스트를 위한 클라이언트 코드
import aiohttp
import asyncio


async def test_workflow():
    async with aiohttp.ClientSession() as session:
        # Node A 호출
        workflow_request = {
            "node_id": "test_workflow_1",
            "input_data": {"test_param": "Hello, Workflow!"},
            "request_id": str(uuid.uuid4())
        }

        async def call_api(url, data):
            async with session.post(url, json=data) as response:
                return await response.json()

        # Node A (Start)
        response_a = await call_api("http://localhost:10001/workflow/start", workflow_request)
        print("Node A Response:", json.dumps(response_a, indent=2))

        # Node B
        response_b = await call_api("http://localhost:10002/process", {
            **workflow_request,
            "input_data": response_a["data"]
        })
        print("Node B Response:", json.dumps(response_b, indent=2))

        # Parallel execution of Node C and D
        tasks = [
            call_api("http://localhost:10003/process", {
                **workflow_request,
                "input_data": response_b["data"]
            }),
            call_api("http://localhost:10004/process", {
                **workflow_request,
                "input_data": response_b["data"]
            })
        ]
        responses_cd = await asyncio.gather(*tasks)
        print("Node C Response:", json.dumps(responses_cd[0], indent=2))
        print("Node D Response:", json.dumps(responses_cd[1], indent=2))

        # Node E (Aggregation)
        response_e = await call_api("http://localhost:10011/aggregate", {
            **workflow_request,
            "input_data": {
                "node_b": response_b["data"],
                "node_c": responses_cd[0]["data"],
                "node_d": responses_cd[1]["data"]
            }
        })
        print("Final Response:", json.dumps(response_e, indent=2))


# 실행 방법 (멀티프로세스로 각 노드 실행)
if __name__ == "__main__":
    import multiprocessing

    # 각 노드를 별도 프로세스로 실행
    processes = [
        multiprocessing.Process(target=run_node_a),
        multiprocessing.Process(target=run_node_b),
        multiprocessing.Process(target=run_node_c),
        multiprocessing.Process(target=run_node_d),
        multiprocessing.Process(target=run_node_e),
        multiprocessing.Process(target=run_node_f),
        multiprocessing.Process(target=run_node_g),
        multiprocessing.Process(target=run_node_h),
        multiprocessing.Process(target=run_node_i),
        multiprocessing.Process(target=run_node_j)
        # multiprocessing.Process(target=run_node_z)
    ]

    # 프로세스 시작
    for p in processes:
        p.start()
    run_node_z()
    # 테스트 실행
    # asyncio.run(test_workflow())

    # 프로세스 종료
    # for p in processes:
    #     p.join()



