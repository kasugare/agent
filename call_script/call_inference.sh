# time curl -d '{"request_id":"1234567890", "text_input":"hihihihihi"}' -H "Content-Type: application/json" http://127.0.0.1:18000/api/v1/call_api
# time curl -d '{"request_id":"1234567890", "text_input":"hihihihihi"}' -H "Content-Type: application/json" http://127.0.0.1:18000/api/v1/workflow/run/all
# time curl -d '{"to":"stt_end_node_202504291319.end","request_id":"1234567890","text_input":"hi test summary"}' -H "Content-Type: application/json" http://127.0.0.1:18000/api/v1/workflow/run

 time curl -d '{"from":"classification_model_node_202504291319.class_stt","to":"classification_model_node_202504291319.class_stt","data":"메롱","shape":"3"}' -H "Content-Type: application/json" http://127.0.0.1:18000/api/v1/workflow/run
# time curl -d '{"from":"stt_start_node_202504291319.start","request_id":"1234567890","text_input":"hi test summary"}' -H "Content-Type: application/json" http://127.0.0.1:18000/api/v1/workflow/run
# time curl -d '{"from":"classification_model_node_202504291319.class_stt"}' -H "Content-Type: application/json" http://127.0.0.1:18000/api/v1/workflow/run
# time curl -d '{"from":"stt_summary_model_node_202504291319.sum_stt","to":"classification_model_node_202504291319.class_stt"}' -H "Content-Type: application/json" http://127.0.0.1:18000/api/v1/workflow/run
# time curl -d '{"from":"stt_start_node_202504291319.start","to":"stt_aggregator_202504291319.aggregation","text_input":"hihi test summary"}' -H "Content-Type: application/json" http://127.0.0.1:18000/api/v1/workflow/run
# time curl -d '{"from":"stt_summary_model_node_202504291319.sum_stt","to":"test_aggregator_202504291319.aggregation","text_input":"hihi test summary"}' -H "Content-Type: application/json" http://127.0.0.1:18000/api/v1/workflow/run
# time curl -d '{"from":"stt_aggregator_202504291319.aggregation"}' -H "Content-Type: application/json" http://127.0.0.1:18000/api/v1/workflow/run
# time curl -d '{"request_id":"req-part_test","text_input":"hihi test summary"}' -H "Content-Type: application/json" http://127.0.0.1:18000/api/v1/workflow/run
