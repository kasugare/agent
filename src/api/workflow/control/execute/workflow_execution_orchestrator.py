#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.control.execute.task_state import TaskState
from api.workflow.control.execute.env_template import AutoTemplateRenderer
from api.workflow.protocol.protocol_message import SYS_NODE_STATUS
from jinja2 import Template, meta, Environment
from threading import Thread
import traceback
import time


class WorkflowExecutionOrchestrator:
    def __init__(self, logger, datastore, meta_pack, job_Q, stream_Q=None):
        self._logger = logger
        self._datastore = datastore
        self._meta_pack = meta_pack
        self._job_Q = job_Q
        self._stream_Q = stream_Q

    def _get_next_service_ids(self, service_id):
        edges_graph = self._meta_pack['act_forward_graph']
        next_service_ids = edges_graph.get(service_id)
        if not next_service_ids:
            next_service_ids = []
        return next_service_ids

    def _get_prev_service_ids(self, service_id):
        prev_edges_graph = self._meta_pack['act_backward_graph']
        prev_service_ids = prev_edges_graph.get(service_id)
        return prev_service_ids

    def _map_template(self, service_id, text_value):
        if not isinstance(text_value, str):
            return text_value
        env = Environment()
        ast = env.parse(text_value)
        ref_keys = meta.find_undeclared_variables(ast)
        value_map = {}
        for ref_key in ref_keys:
            try:
                value_id = f"I.{service_id}.{ref_key}"
                ref_value = self._datastore.get_param_value_service(value_id)
                value_map[ref_key] = ref_value
            except:
                pass

        if value_map:
            renderer = AutoTemplateRenderer(self._logger)
            rederer_info = renderer.auto_render(text_value, value_map)
        return text_value

    def _get_envs(self, service_id):
        try:
            service_pool = self._meta_pack['service_pool']
            service_info = service_pool.get(service_id)
            module_info = service_info.get('module_info')
            if not module_info:
                return {}

            sys_env_map = module_info.get('sys_environments')
            if not sys_env_map:
                return {}

            env_params_info = sys_env_map.get('params')
            if not env_params_info:
                return {}

            node_id = service_info.get('node_id')
            env_params_map = {env_param_map.get('key'): f"E.{node_id}.{env_param_map.get('key')}"
                             for env_param_map in env_params_info if env_param_map.get('key')}
            for env_name, env_value_id in env_params_map.items():
                env_value = self._datastore.get_param_value_service(env_value_id)
                env_params_map[env_name] = self._map_template(service_id, env_value)
            return env_params_map
        except Exception as e:
            return {}

    def _get_assets(self, service_id):
        try:
            service_pool = self._meta_pack['service_pool']
            service_info = service_pool.get(service_id)
            module_info = service_info.get('module_info')
            if not module_info:
                return {}

            asset_env_map = module_info.get('asset_environments')
            if not asset_env_map:
                return {}

            asset_params_info = asset_env_map.get('params')
            if not asset_params_info:
                return {}

            node_id = service_info.get('node_id')
            asset_params_map = {asset_param_map.get('key'): f"A.{node_id}.{asset_param_map.get('key')}"
                             for asset_param_map in asset_params_info if asset_param_map.get('key')}
            for asset_name, asset_value_id in asset_params_map.items():
                env_value = self._datastore.get_param_value_service(asset_value_id)
                asset_params_map[asset_name] = self._map_template(service_id, env_value)
            return asset_params_map
        except Exception as e:
            return {}

    def _extract_forced_param_value(self, service_id, param_name):
        value_id = f"O.{service_id}.{param_name}"
        extract_param_value = self._datastore.get_param_value_service(value_id)
        return extract_param_value

    def _extract_param_value(self, service_id, param_map_list) -> dict:
        params = {}
        for param_map in param_map_list:
            param_name = param_map.get('key')
            if 'value' in param_map.keys():
                if param_map.get('refer_type') == 'direct':
                    value_id = f"I.{service_id}.{param_name}"
                else:
                    addr_value = param_map.get('value')
                    value_id = f"O.{addr_value}"
                extract_params_value = self._datastore.get_param_value_service(value_id)
                params[param_name] = extract_params_value
            elif 'values' in param_map.keys():
                value_param_map_list = param_map.get('values')
                sub_service_id = f"{service_id}.{param_name}"
                sub_params = self._extract_param_value(sub_service_id, value_param_map_list)
                params.update({param_name:sub_params})
        return params

    def _get_params(self, service_id):
        def get_edge_params(edge_param_id, edges_param_map):
            param_map_list = edges_param_map.get(edge_param_id)
            params = {}
            if not param_map_list:
                return params
            params = self._extract_param_value(service_id, param_map_list)
            return params

        backward_graph = self._meta_pack['backward_graph']
        prev_service_ids = backward_graph.get(service_id)
        edges_param_map = self._meta_pack['act_edges_param_map']
        param_map = {}
        if not prev_service_ids:
            edge_params_id = f"None-{service_id}"
            param_map = get_edge_params(edge_params_id, edges_param_map)
            prev_service_ids = []

        for prev_service_id in prev_service_ids:
            edge_params_id = f"{prev_service_id}-{service_id}"
            param_map = get_edge_params(edge_params_id, edges_param_map)
        return param_map

    def _get_start_nodes(self):
        start_nodes = self._meta_pack['act_start_nodes']
        return start_nodes

    def _get_end_nodes(self):
        end_nodes = self._meta_pack['act_end_nodes']
        return end_nodes

    def _set_start_jobs(self, request_params):
        start_service_ids = self._get_start_nodes()
        for start_service_id in start_service_ids:
            self._datastore.set_service_params_service(start_service_id, request_params)
            self._job_Q.put_nowait(start_service_id)

    def _result_mapper(self, service_id, result):
        service_pool = self._meta_pack['service_pool']
        results_schema = service_pool[service_id]['result']
        result_map = {}
        if isinstance(result, dict):
            schema_keys = [schema_map.get('key') for schema_map in results_schema if schema_map.get('key')]
            res_keys = list(result.keys())
            inter_res_keys = list(set(res_keys).intersection(set(schema_keys)))
            for res_key in inter_res_keys:
                result_map[res_key] = result.get(res_key)
        elif isinstance(result, list) or isinstance(result, tuple):
            schema_keys = [schema_map.get('key') for schema_map in results_schema if schema_map.get('key')]
            for _index, res_key in enumerate(schema_keys):
                result_map[res_key] = result[_index]
        else:
            for schema in results_schema:
                result_name = schema['key']
                result_map[result_name] = result

        custom_result_meta = self._datastore.get_custom_result_meta_by_service_id_service(service_id)
        if custom_result_meta:
            for result_meta in custom_result_meta:
                refer_type = result_meta.get('refer_type')
                custom_key = result_meta.get('key')
                if refer_type.lower() == 'indirect':
                    ref_value_id = result_meta.get('value')
                    value = self._datastore.find_io_value_service(ref_value_id)
                else:
                    value = result_meta.get('value')
                result_map[custom_key] = value
        return result_map

    def _check_all_completed(self, task_map):
        be_completed = True
        for k, task in task_map.items():
            if task.get_state() != TaskState.COMPLETED:
                be_completed = False
                break
        return be_completed

    def _execute_task(self, task):
        try:
            task.execute()
            service_id = task.get_service_id()
            self._job_Q.put_nowait(service_id)
        except Exception as e:
            self._logger.error(e)

    def _timeout(self, timeout):
        time.sleep(timeout)
        self._job_Q.put_nowait("SIGTERM")

    def _run_exec_handler(self, task_map, request_id=None):
        result = None
        start_ts = time.time()
        while True:
            try:
                self._logger.debug("<<< WAIT Q >>>")
                service_id = self._job_Q.get()
                if service_id == "SIGTERM":
                    self._logger.error("Exit process")
                    break
                task = task_map.get(service_id)
                task_state = task.get_state()

                if self._stream_Q:
                    splited_service_id = service_id.split('.')
                    node_id = splited_service_id[0]
                    service_name = splited_service_id[1]
                    status = str(task_state).split('.')[1]
                    status_message = SYS_NODE_STATUS(request_id, node_id, service_name, status, int(time.time()))
                    self._stream_Q.put_nowait(status_message)
                    time.sleep(0.1)

                if task_state in [TaskState.PENDING]:
                    self._logger.debug(f" - Step 1. [PENDING  ] wait order to run: {service_id}")
                    task.set_state(TaskState.SCHEDULED)
                    self._job_Q.put_nowait(service_id)

                elif task_state in [TaskState.SCHEDULED]:
                    self._logger.debug(f" - Step 2. [SCHEDULED] prepared service resources: {service_id}")
                    task.set_state(TaskState.QUEUED)
                    self._job_Q.put_nowait(service_id)

                elif task_state in [TaskState.QUEUED]:
                    self._logger.debug(f" - Step 3. [QUEUED   ] aggregation params and run: {service_id}")
                    runnable = True
                    prev_service_ids = self._get_prev_service_ids(service_id)
                    if prev_service_ids:
                        for prev_service_id in prev_service_ids:
                            prev_task = task_map.get(prev_service_id)
                            if prev_task.get_state() not in [TaskState.COMPLETED, TaskState.SKIPPED]:
                                runnable = False
                    else:
                        runnable = True

                    if runnable:
                        env_params = self._get_envs(service_id)
                        task.set_env_params(env_params)

                        asset_params = self._get_assets(service_id)
                        task.set_asset_params(asset_params)

                        func_params = self._get_params(service_id)
                        if task.get_role() == 'generation':
                            param_value = self._extract_forced_param_value(service_id, "messages")
                            func_params['messages'] = param_value

                        task.set_params(func_params)
                        task.set_state(TaskState.RUNNING)
                        self._datastore.set_service_params_service(service_id, func_params)
                        self._job_Q.put_nowait(service_id)
                elif task_state in [TaskState.RUNNING]:
                    if task.get_location() == 'inner':
                        self._execute_task(task)
                    else:
                        executor = Thread(target=self._execute_task, args=(task,))
                        executor.start()

                elif task_state in [TaskState.COMPLETED]:
                    self._logger.debug(f" - Step 4. [COMPLETED] done task execution : {service_id}")
                    task_result = task.get_result()
                    customed_task_result = self._result_mapper(service_id, task_result)
                    task = task_map.get(service_id)
                    task.set_result(customed_task_result)

                    self._datastore.set_service_result_service(service_id, customed_task_result)
                    next_service_ids = self._get_next_service_ids(service_id)
                    for next_service_id in next_service_ids:
                        self._job_Q.put_nowait(next_service_id)

                    if self._check_all_completed(task_map):
                        end_service_ids = self._get_end_nodes()
                        for end_service_id in end_service_ids:
                            end_task = task_map.get(end_service_id)
                            result = end_task.get_result()
                        break

                elif task_state in [TaskState.FAILED]:
                    self._logger.debug(f" - Step 5. [FAILED   ] paused task by user : {service_id}")
                    self._show_task(task_map)
                    break

                elif task_state in [TaskState.PAUSED]:
                    self._logger.debug(f" - Step 6. [PAUSED   ] paused task by user : {service_id}")
                    break

                elif task_state in [TaskState.STOPPED]:
                    self._logger.debug(f" - Step 7. [STOP     ] stop task by user : {service_id}")
                    break

                elif task_state in [TaskState.SKIPPED]:
                    self._logger.debug(f" - Step 8. [SKIPPED  ] skipped task: {service_id}")
                    break

                elif task_state in [TaskState.BLOCKED]:
                    self._logger.debug(f" - Step 9. [BLOCKED  ] blocked task: {service_id}")
                    break
                else:
                    break
                self._show_task(task_map)
                # self._show_task_info(task)
            except Exception as e:
                self._logger.error(e)
                self._logger.error(traceback.print_exc())
                break
        end_ts = time.time()
        duration = "%0.2f" %(end_ts - start_ts)
        self._logger.info(f"--- # Request Job Completed, Duration: {duration}s ---")
        self._logger.info(f" - Result: {result}")
        self._show_task(task_map)
        return result

    def run_workflow(self, request_params):
        self._logger.critical(f" # user params: {request_params}")
        request_id = request_params.get('request_id')
        self._set_start_jobs(request_params)
        task_map = self._meta_pack.get('act_task_map')
        result = self._run_exec_handler(task_map, request_id)
        return result

    def _show_task(self, task_map):
        for service_id, task in task_map.items():
            self._logger.warn(f" - [{task.get_state()}] {service_id}")

    def _show_task_info(self, task):
        service_id = task.get_service_id()
        service_role = task.get_role()
        self._logger.debug(f" - service_id: {service_id}")
        self._logger.debug(f" - role: {service_role}")
        self._logger.debug(f" - envs: {task.get_env_params()}")
        self._logger.debug(f" - params: {task.get_params()}")
        self._logger.debug(f" - State: {task.get_state()}")
        self._logger.debug(f" - Error: {task.get_error()}")
        self._logger.debug(f" - Result: {task.get_result()}")
