# RAG
#time curl -H "Content-Type: application/json" -H "secret_key: secret" -H "user_id: test_user" -H "request_id: requset1234" -H "session_id: session1234" http://127.0.0.1:8080/api/v1/workflow/run -d '{"from_node": "Input_zla_r0_node.query_input", "to_node": "Output_OvdARr_node.output", "parameter": {"query": "에이전트의 기본 구성 요소는?"}}'

time curl -d '{"request_id":"1234567890", "query":"에이전트의 기본 구성 요소는?"}' -H "Content-Type: application/json" http://127.0.0.1:8080/api/v1/workflow/run

