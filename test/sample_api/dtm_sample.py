#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uvicorn
from datetime import datetime
import asyncio
import uuid
import json
import random
import time


# 데이터 모델 정의
class WorkflowStartRequest(BaseModel):
    node_id: str
    input_data: str
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


app_node_a = FastAPI(title="Node A - API Gateway")


class WorkflowMergeResponse(BaseModel):
    request_id: str
    node_id: str
    status: str
    data: Dict[str, Any]
    timestamp: str


# Node A (Start Node) - API Gateway
class NodeA_Model(BaseModel):
    tar_path: str

@app_node_a.post("/process/node_a")#, response_model=WorkflowResponse)
async def process_node(request: NodeA_Model):
    print(request)
    print("#" * 100)
    print(f"< Node A >")
    print(f"  L PARAMS: {request.tar_path}")
    # time.sleep(10)
    response = {
        "tif_path": "/data/2026_01_16/033500010101722969020240422093257001_1/in_tar_file/033500010101722969020240422093257001_1_merged.tif",
        "txt_path": "/data/2026_01_16/033500010101722969020240422093257001_1/in_tar_file/03B100094800000000020251201091648714.txt",
        "timestamp": datetime.now().isoformat()
    }
    return response


# Node B - Business Logic 1
class NodeB_Model(BaseModel):
    tif_path: str

app_node_b = FastAPI(title="Node B - Business Logic 1")
@app_node_b.post("/process/node_b")#, response_model=WorkflowResponse)
async def process_node(request: NodeB_Model):
    print(f"< Node B >")
    print(f"  L PARAMS: {request.tif_path}")
    # time.sleep(5)
    await asyncio.sleep(random.randrange(1, 5)*0.1)

    response = {
        "img_path": "/data/2026_01_16/033500010101722969020240422093257001_1_merged",
        "doccls_json_path": "/data/2026_01_16/033500010101722969020240422093257001_1_merged/033500010101722969020240422093257001_1_merged_doccls.json",
        "lc_img_list": [
            "/data/2026_01_16/033500010101722969020240422093257001_1_merged/033500010101722969020240422093257001_1_merged_6.png",
            "/data/2026_01_16/033500010101722969020240422093257001_1_merged/033500010101722969020240422093257001_1_merged_8.png"
        ],
        "timestamp": datetime.now().isoformat()
    }
    return response


# Node C - Business Logic 2
class NodeC_Model(BaseModel):
    img_path: str
    doccls_json_path: str

app_node_c = FastAPI(title="Node C - Business Logic 2")
@app_node_c.post("/process/node_c")#, response_model=WorkflowResponse)
async def process_node(request: NodeC_Model):
    print(f"< Node C >")
    print(f"  L PARAMS: {request.img_path}")
    print(f"  L PARAMS: {request.doccls_json_path}")
    # time.sleep(5)
    await asyncio.sleep(random.randrange(1, 5)*0.1)

    response = {
        "extr_json_path": "/data/2026_01_16/033500010101722969020240422093257001_1_merged/033500010101722969020240422093257001_1_merged_extr.json",
        "timestamp": datetime.now().isoformat()
    }
    return response


# Node D - Business Logic 3
class NodeD_Model(BaseModel):
    img_path: str
    doccls_json_path: str
    extr_json_path: str

app_node_d = FastAPI(title="Node D - Business Logic 3")
@app_node_d.post("/process/node_d")#, response_model=WorkflowResponse)
async def process_node(request: NodeD_Model):
    print(f"< Node D >")
    print(f"  L PARAMS: {request.img_path}")
    print(f"  L PARAMS: {request.doccls_json_path}")
    print(f"  L PARAMS: {request.extr_json_path}")
    # time.sleep(5)
    await asyncio.sleep(random.randrange(1, 5) * 0.1)

    response = {
        "save_FEtype_path": "/data/2026_01_16/033500010101722969020240422093257001_1_merged/033500010101722969020240422093257001_1_merged_FE.json",
        "timestamp": datetime.now().isoformat()
    }
    return response


# Node E - Business Logic 3
class NodeE_Model(BaseModel):
    img_path: str
    lc_img_list: list

app_node_e = FastAPI(title="Node E - Business Logic 4")
@app_node_e.post("/process/node_e")#, response_model=WorkflowResponse)
async def process_node(request: NodeE_Model):
    print(f"< Node E >")
    print(f"  L PARAMS: {request.img_path}")
    print(f"  L PARAMS: {request.lc_img_list}")
    await asyncio.sleep(random.randrange(1, 5) * 0.1)

    response = {
        "ocr_json_path_list": [
            "/data/2026_01_16/033500010101722969020240422093257001_1_merged/ocr/033500010101722969020240422093257001_1_merged_6.json",
            "/data/2026_01_16/033500010101722969020240422093257001_1_merged/ocr/033500010101722969020240422093257001_1_merged_8.json"
        ],
        "timestamp": datetime.now().isoformat()
    }
    return response


# Node F - Business Logic 3
class NodeF_Model(BaseModel):
    lc_img_list: list
    ocr_json_path_list: list

app_node_f = FastAPI(title="Node F - Business Logic 5")
@app_node_f.post("/process/node_f")#, response_model=WorkflowResponse)
async def process_node(request: NodeF_Model):
    print(f"< Node F >")
    print(f"  L PARAMS: {request.lc_img_list}")
    print(f"  L PARAMS: {request.ocr_json_path_list}")
    await asyncio.sleep(random.randrange(1, 5) * 0.1)

    response = {
        "lc_number": "033500010101722969020240422093257001_1_merged",
        "result_path": "/data/2026_01_16/033500010101722969020240422093257001_1_merged/033500010101722969020240422093257001_1_merged_nlp_extr_result.json",
        "timestamp": datetime.now().isoformat()
    }
    return response

# Node G - Business Logic 3
class NodeG_Model(BaseModel):
    text_path: str

app_node_g = FastAPI(title="Node G - Business Logic 6")
@app_node_g.post("/process/node_g")#, response_model=WorkflowResponse)
async def process_node(request: NodeG_Model):
    print(f"< Node G >")
    print(f"  L PARAMS: {request.text_path}")
    await asyncio.sleep(random.randrange(1, 5) * 0.1)

    response = {
        "lc_number": "03B100094800000000020251201091648714",
        "result_path": "/data/2026_01_16/033500010101722969020240422093257001_1/in_tar_file/03B100094800000000020251201091648714_nlp_extr_result.json",
        "timestamp": datetime.now().isoformat()
    }
    return response


# Node H - Business Logic 3
class NodeH_Model(BaseModel):
    nlp_img_lc_path: Optional[str] = None
    nlp_text_lc_path: Optional[str] = None
    aiv_img_path: Optional[str] = None

app_node_h = FastAPI(title="Node H - Business Logic 7")
@app_node_h.post("/process/node_h")#, response_model=WorkflowResponse)
async def process_node(request: NodeH_Model):
    print(f"< Node H >")
    print(f"  L PARAMS: {request.nlp_img_lc_path}")
    print(f"  L PARAMS: {request.nlp_text_lc_path}")
    print(f"  L PARAMS: {request.aiv_img_path}")
    await asyncio.sleep(random.randrange(1, 5) * 0.1)

    response = {
        "result_path": "/data/2026_01_16/033500010101722969020240422093257001_1_merged/lc_meta.json",
        "timestamp": datetime.now().isoformat()
    }
    return response


# Node z - Result Aggregator
app_node_z = FastAPI(title="Node E - Result Aggregator 3")
@app_node_z.post("/aggregate")#, response_model=WorkflowResponse)
async def aggregate_results(request: WorkflowRequest):
    print(f"# Node Z - {request.input_data}")

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


def run_node_z():
    uvicorn.run(app_node_z, host="127.0.0.1", port=10020)


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
        multiprocessing.Process(target=run_node_h)
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
