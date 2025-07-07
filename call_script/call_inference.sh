#time curl -d '{"request_id":"1234567890", "text_input":"hihihihihi"}' -H "Content-Type: application/json" http://127.0.0.1:18000/api/v1/call_api
#time curl -d '{"request_id":"1234567890", "text_input":"hihihihihi"}' -H "Content-Type: application/json" http://127.0.0.1:18000/api/v1/workflow/run/all
#time curl -d '{"from":"stt_start_node_202504291319.start", "to":"stt_end_node_202504291319.end"}' -H "Content-Type: application/json" http://127.0.0.1:18000/api/v1/workflow/run/part
#time curl -d '{"from":"stt_start_node_202504291319.start","to":"stt_start_node_202504291319.start"}' -H "Content-Type: application/json" http://127.0.0.1:18000/api/v1/workflow/run/part
time curl -d '{"from":"stt_start_node_202504291319.start","to":"stt_aggregator_202504291319.aggregation"}' -H "Content-Type: application/json" http://127.0.0.1:18000/api/v1/workflow/run/part
#time curl -d '{"from":"stt_aggregator_202504291319.aggregation"}' -H "Content-Type: application/json" http://127.0.0.1:18000/api/v1/workflow/run/part
#time curl -d '{"from":"classification_model_node_202504291319.class_stt"}' -H "Content-Type: application/json" http://127.0.0.1:18000/api/v1/workflow/run/part
