time curl -H "Content-Type: application/json" -H "secret_key: secret" -H "user_id: test_user" -H "request-id: requset1234" -H "session-id: session1234" http://127.0.0.1:8080/api/v1/workflow/inference -d '{"parameter": {"query": "/data/sample/033500010101722969020240422093257001_1.tar"}}'

#time curl -d '{"request_id":"1234567890", "query":"에이전트의 기본 구성 요소는?"}' -H "Content-Type: application/json" http://127.0.0.1:8080/api/v1/workflow/inference

