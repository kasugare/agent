#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.common.api_requester.external_api_requester import ExternalApiRequester
from api.workflow.service.meta.meta_store_service import MetaStoreService
from api.workflow.service.data.data_store_service import DataStoreService
from api.workflow.service.task.task_store_service import TaskStoreService


class MetricService:
    def __init__(self, logger):
        self._logger = logger

    def _gen_store_pack(self, wf_id, job_id):
        store_pack = {}
        metastore = MetaStoreService(self._logger, wf_id)
        datastore = DataStoreService(self._logger, job_id)
        taskstore = TaskStoreService(self._logger, job_id)
        store_pack['metastore'] = metastore
        store_pack['datastore'] = datastore
        store_pack['taskstore'] = taskstore
        return store_pack

    def _cvt_params(self, request, body={}):
        params = {}
        if request and request.headers:
            params.update(dict(request.headers))
        if body:
            params.update(dict(body))
        self._logger.debug("Input Params")
        for k, v in params.items():
            self._logger.warn(f" - {k}: {v}")
        return params

    def extract_io_data(self, datastore):
        data_pool = datastore.get_service_data_pool_service()
        d = dict(sorted(data_pool.items()))
        for k, v in d.items():
            splited_key = k.split(".")
            in_type = splited_key[0]
            service_id = (".").join(splited_key[1:])
            self._logger.info(f"  L [{in_type}] {service_id} : {v}")
        return data_pool

    def extract_active_dag(self, workflow_executor):
        act_meta = workflow_executor.get_act_meta()
        for k, v in act_meta.items():
            self._logger.info(f" - {k}")
            if isinstance(v, dict):
                for kk, vv in v.items():
                    self._logger.debug(f" \t- {kk}: {vv}")
            elif isinstance(v, list):
                for l in v:
                    self._logger.debug(f" \t- {l}")
            else:
                self._logger.debug(f" \t- {v}")
            self._logger.debug("*" * 200)
        return act_meta

    def extract_active_task_pool(self, workflow_executor):
        act_meta = workflow_executor.get_act_meta()
        act_task_map = act_meta.get('act_task_map')
        if not act_task_map:
            return

        for task_id, task_obj in act_task_map.items():
            self._logger.info(f" - {task_id}")
            service_id = task_obj.get_service_id()
            state = task_obj.get_state()
            env = task_obj.get_env_params()
            params = task_obj.get_params()
            result = task_obj.get_result()
            error = task_obj.get_error()
            node_type = task_obj.get_node_type()
            self._logger.debug(f"\t- service_id: {service_id}")
            self._logger.debug(f"\t- state:      {state}")
            self._logger.debug(f"\t- env:        {env}")
            self._logger.debug(f"\t- params:     {params}")
            self._logger.debug(f"\t- result:     {result}")
            self._logger.debug(f"\t- Error:      {error}")
            self._logger.debug(f"\t- node_type:  {node_type}")
            task_obj.print_service_info()
            self._logger.debug("*" * 100)
        return act_task_map

    def extract_job_state(self, job_id):
        def is_completed(task_state: dict):
            if task_state in ["TaskState.COMPLETED", "TaskState.SKIPPED"]:
                return True
            return False

        def has_error(task_state: dict):
            if task_state in ["TaskState.FAILED"]:
                return True
            return False

        def is_stopped(task_state: dict):
            if task_state in ["TaskState.STOPPED"]:
                return True
            return False

        job_status = {}
        taskstore = TaskStoreService(self._logger, job_id)
        task_state_map = taskstore.get_workflow_status()

        is_completed = all(is_completed(task_state) for task_state in task_state_map.values())
        if is_completed:
            job_status["status"] = "COMPLETED"

        has_error = all(has_error(task_state) for task_state in task_state_map.values())
        if has_error:
            job_status["status"] = "FAILED"

        is_stopped = all(is_stopped(task_state) for task_state in task_state_map.values())
        if is_stopped:
            job_status["status"] = "STOPPED"

        processing_time_map = taskstore.get_processing_time()
        job_status["processing_time"] = processing_time_map

        for state_key, state_value in job_status.items():
            if isinstance(state_value, dict):
                self._logger.debug(f" - {state_key}")
                for k, v in state_value.items():
                    self._logger.debug(f"    L {k}: {v}")
            else:
                self._logger.debug(f" - {state_key}: {state_value}")
        return job_status

    def check_working_state(self, wf_id):
        def is_available(queue_info):
            available_stat = queue_info.get('available', 0)
            if available_stat > 0:
                return True
            return False

        external_api = ExternalApiRequester(self._logger)
        metastore = MetaStoreService(self._logger, wf_id)
        nodes_meta = metastore.get_nodes_meta_service()
        status_map = {}
        for node_id, node_map in nodes_meta.items():
            node_type = node_map.get('node_type')
            if node_type == 'external':
                api_info = node_map.get('api_info', {})
                base_url = api_info.get('base_url')
                gateway_info = external_api.call_api_sync(base_url=base_url, method='get', route_path='/_gateway/metrics')
                servers_stat = gateway_info.get('backend_servers')
                status_map[node_id] = servers_stat
                self._logger.debug(f" - {node_id}: {servers_stat}")
        is_working = (lambda x: not x)(all(is_available(queue_info) for queue_info in status_map.values()))
        result = {
            "is_working": is_working
        }
        return result




