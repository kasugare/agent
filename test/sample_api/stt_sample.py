from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uvicorn
from datetime import datetime
import asyncio
import uuid
import json
import random



#------------------------------------------------------------------------#
# Node A (Start Node) - API Gateway

class StartRequest(BaseModel):
	src_stt: str
	request_id: Optional[str] = None

class StartResponse(BaseModel):
	output: Dict[str, Any]

app_node_a = FastAPI(title="Node A - Start Node")
@app_node_a.post("/v1/stt_start", response_model=StartResponse)
async def start(request: StartRequest):
	print("#" * 100)
	print(f"# Node A: stt_start_node_202504291319")
	request_id = request.request_id or str(uuid.uuid4())

	response = {
		"src_stt": """요약전 대화 내용"""
	}

	return response


#------------------------------------------------------------------------#
# Node B - Business Logic 1

class TestRequest(BaseModel):
	input_key_1: str
	input_key_2: str

class TestResponse(BaseModel):
	result_key: str

app_node_b = FastAPI(title="Node B - Test Node")
@app_node_b.post("/v1/test", response_model=TestResponse)
async def test_name(request: TestRequest):
	print(f"# Node B - {request}")
	await asyncio.sleep(random.randrange(1, 5)*0.01)

	res = TestResponse(
		result_key="request.request_id"
	)
	return res



#------------------------------------------------------------------------#
# Node C - Business Logic 2

class SumInputRequest(BaseModel):
	text_input: str
	max_tokens: int

class SumHealthResponse(BaseModel):
	status: int

class SumDeployModelCheckResponse(BaseModel):
	result: List[Any]

class SumResultResponse(BaseModel):
	model_name: str
	model_version: str
	text_output: str

app_node_c = FastAPI(title="Node C - stt_summary_model_node_202504291319")
@app_node_c.post("/v2/helath/ready", response_model=SumHealthResponse)
async def sum_health_check():
	print(f"# Node C - health_check()")
	await asyncio.sleep(random.randrange(1, 5)*0.01)
	return SumHealthResponse(
		status=1
	)

@app_node_c.post("/v2/repository/index", response_model=SumDeployModelCheckResponse)
async def sum_deploy_model_check():
	print(f"# Node C - deploy_model_check()")
	await asyncio.sleep(random.randrange(1, 5)*0.01)
	return SumDeployModelCheckResponse(
		result = ["1", "2", "3"]
	)

@app_node_c.post("/v2/models/stt/generate", response_model=SumResultResponse)
async def sum_stt(request: SumInputRequest):
	print(f"# Node C - sum_stt(): {request}")
	await asyncio.sleep(random.randrange(1, 5)*0.01)
	return SumResultResponse(
		model_name = "요약모델",
		model_version = "1.1.0",
		text_output = f"{request.text_input}-->주절주절요약!"
	)



#------------------------------------------------------------------------#
# Node D - Business Logic 3

class ClassInputRequest(BaseModel):
	name: str
	shape: str#List[Any]
	datatype: str
	data: str

class ClassHealthResponse(BaseModel):
	status: int

class ClassDeployModelCheckResponse(BaseModel):
	result: List

class ClassResultResponse(BaseModel):
	model_name: str
	model_version: str
	data: str

app_node_d = FastAPI(title="Node D - classification_model_node_202504291319")
@app_node_d.post("/v2/helath/ready", response_model=SumHealthResponse)
async def cls_health_check():
	print(f"# Node D - cls_health_check()")
	await asyncio.sleep(random.randrange(1, 5)*0.01)
	return SumHealthResponse(
		status = 1
	)

@app_node_d.post("/v2/repository/index", response_model=ClassDeployModelCheckResponse)
async def cls_deploy_model_check():
	print(f"# Node D - cls_deploy_model_check()")
	await asyncio.sleep(random.randrange(1, 5)*0.01)
	return ClassDeployModelCheckResponse(
		result = ["A", "B", "C"]
	)

@app_node_d.post("/v2/models/vert_base_smry_cls/infer", response_model=ClassResultResponse)
async def cls_stt(request: ClassInputRequest):
	print(f"# Node D - cls_stt()")
	await asyncio.sleep(random.randrange(1, 5)*0.01)
	print(f"  - {request.name}")
	print(f"  - {request.shape}")
	print(f"  - {request.datatype}")
	print(f"  - {request.data}")

	return ClassResultResponse(
		model_name = "분류모델",
		model_version = "2.2.0",
		data = "CDC25380"
	)


#------------------------------------------------------------------------#
# Node E - Business Logic 3

class AggInputRequest(BaseModel):
	summery_stt: str
	cls_code: str

class AggResultResponse(BaseModel):
	result_data: str

app_node_e = FastAPI(title="Node E - stt_aggregator_202504291319")
@app_node_e.post("/v1/result/aggregator", response_model=AggResultResponse)
async def aggregator(request: AggInputRequest):
	print(f"# Node E - aggregator()")
	await asyncio.sleep(random.randrange(1, 5)*0.1)

	result = f"요약내용: {request.summery_stt} - 분류코드: {request.cls_code}"

	return AggResultResponse(
		result_data = result
	)




#------------------------------------------------------------------------#
# Node F - Business Logic 3

class TestAggInputRequest(BaseModel):
	agg_result: str #Dict[str, Any]
	test_aggr: str

class TestAggResultResponse(BaseModel):
	result_data: Dict[str, Any]

app_node_f = FastAPI(title="Node F - test_aggregator_202504291319")
@app_node_f.post("/v1/result/test_aggregator", response_model=TestAggResultResponse)
async def aggregation(request: TestAggInputRequest):
	print(f"# Node F - aggregator()")
	import time
	await asyncio.sleep(random.randrange(1, 5)*0.02)
	splited_agg_result = request.agg_result.split('-')

	result_data = {
			'summary': splited_agg_result[0],
			'cls_code': splited_agg_result[-1],
			"combo": {
				"STT_TS": int(time.time() * 1000),
				"params": request
			}
		}
	return TestAggResultResponse(result_data=result_data)


#------------------------------------------------------------------------#
# Node G - Business Logic 3

class EndInputRequest(BaseModel):
	result: Dict[str, Any]

class EndResultResponse(BaseModel):
	result: Dict[str, Any]

app_node_g = FastAPI(title="Node G - stt_end_node_202504291319")
@app_node_g.post("/process", response_model=EndResultResponse)
async def end(request: EndInputRequest):
	print(f"# Node G - end()")
	await asyncio.sleep(random.randrange(1, 5)*0.01)

	result = request.result

	return EndResultResponse(
		result = result
	)


#------------------------------------------------------------------------#
# Node z - Result Aggregator

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


#------------------------------------------------------------------------#

# 각 노드별 서버 실행을 위한 설정
def run_node_a():
	uvicorn.run(app_node_a, host="127.0.0.1", port=20001)


def run_node_b():
	uvicorn.run(app_node_b, host="127.0.0.1", port=20002)


def run_node_c():
	uvicorn.run(app_node_c, host="127.0.0.1", port=20003)


def run_node_d():
	uvicorn.run(app_node_d, host="127.0.0.1", port=20004)


def run_node_e():
	uvicorn.run(app_node_e, host="127.0.0.1", port=20005)


def run_node_f():
	uvicorn.run(app_node_f, host="127.0.0.1", port=20006)


def run_node_g():
	uvicorn.run(app_node_g, host="127.0.0.1", port=20007)


def run_node_z():
    uvicorn.run(app_node_z, host="127.0.0.1", port=20011)



#------------------------------------------------------------------------#
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
		response_a = await call_api("http://localhost:20001/workflow/start", workflow_request)
		print("Node A Response:", json.dumps(response_a, indent=2))

		# Node B
		response_b = await call_api("http://localhost:20002/process", {
			**workflow_request,
			"input_data": response_a["data"]
		})
		print("Node B Response:", json.dumps(response_b, indent=2))

		# Parallel execution of Node C and D
		tasks = [
			call_api("http://localhost:20003/process", {
				**workflow_request,
				"input_data": response_b["data"]
			}),
			call_api("http://localhost:20004/process", {
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



#------------------------------------------------------------------------#

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
		multiprocessing.Process(target=run_node_g)
		# multiprocessing.Process(target=run_node_h),
		# multiprocessing.Process(target=run_node_i),
		# multiprocessing.Process(target=run_node_j)
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
