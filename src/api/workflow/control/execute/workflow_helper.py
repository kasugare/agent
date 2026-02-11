#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.control.execute.task_state import TaskState
from api.workflow.control.execute.env_template import AutoTemplateRenderer
from api.workflow.protocol.protocol_message import SYS_NODE_STATUS
from api.workflow.error_pool.error import ExceedExecutionRetryError
from jinja2 import Template, meta, Environment
from multiprocessing import Queue
from threading import Thread
import traceback
import time


class WorkflowHelper:
    def __init__(self, logger, store_pack, meta_pack):
        self._logger = logger
        self._store_pack = store_pack
        self._datastore = store_pack.get('datastore', {})
        self._taskstore = store_pack.get('taskstore', {})
        self._meta_pack = meta_pack

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

    def _set_action_skip_nodes(self, service_id, skip_target_service_ids, depth=0):
        def check_prev_task_state(service_id):
            task_state = self._get_task_state(service_id)
            if task_state in [TaskState.COMPLETED, TaskState.SKIPPED, TaskState.BLOCKED]:
                return True
            else:
                return False
        space = "    " * depth
        self._logger.debug(f"{space} # Service_id: {service_id},  skip_target_service_ids: {skip_target_service_ids}")
        self._logger.debug(f"{space}   L skip target service ids: {skip_target_service_ids}")

        for skip_target_service_id in skip_target_service_ids:
            prev_edges_graph = self._meta_pack['act_backward_graph']
            prev_service_ids = prev_edges_graph.get(skip_target_service_id)
            if all(check_prev_task_state(prev_service_id) for prev_service_id in prev_service_ids):
                self._set_task_state(skip_target_service_id, TaskState.SKIPPED)
                self._logger.error(f"{space}   @ skip service ids: {skip_target_service_id}")

            next_skip_service_ids = self._get_next_service_ids(skip_target_service_id)
            next_depth = depth + 1
            self._set_action_skip_nodes(skip_target_service_id, next_skip_service_ids, next_depth)

    def _get_required_params(self, service_id):
        service_pool = self._meta_pack['service_pool']
        service_info = service_pool.get(service_id, {})
        service_params = service_info.get('params', [])
        required_params = [service_param for service_param in service_params if service_param.get('required', False)]
        return required_params

    def _set_blocked_nodes(self, service_id, depth=0):
        def check_blocked_task_state(edge_param_map):
            key_required = edge_param_map.get('key_required', False)
            refer_type = edge_param_map.get('refer_type')

            if key_required and refer_type == 'indirect':
                value_id = edge_param_map.get('value')
                splited_value_id = value_id.split(".")
                ref_service_id = ".".join(splited_value_id[:-1])
                ref_value = self._datastore.get_output_value(value_id)
                ref_task_state = self._get_task_state(ref_service_id)
                self._logger.debug(f"{space}    - {ref_service_id} : {ref_task_state}")
                self._logger.debug(f"{space}    - {value_id}: {ref_value}")
                if ref_task_state in [TaskState.STOPPED, TaskState.SKIPPED, TaskState.BLOCKED] and ref_value is None:
                    return True
            return False

        space = "    " * depth
        self._logger.debug(f"{space} # Service_id: {service_id}, state: {self._get_task_state(service_id)}")

        edges_param_map = self._meta_pack['act_edges_param_map']
        if self._get_task_state(service_id) == TaskState.PENDING:
            edge_ids = self._get_edge_ids_by_service_id(service_id)
            for edge_id in edge_ids:
                edge_param_map_list = edges_param_map.get(edge_id)
                self._logger.debug(f"{space}   L edge_id:  {edge_id}")
                for edge_param_map in edge_param_map_list:
                    self._logger.debug(f"{space}     - edge_map: {edge_param_map}")
                if any(check_blocked_task_state(edge_param_map) for edge_param_map in edge_param_map_list):
                    self._set_task_state(service_id, TaskState.BLOCKED)
                    self._logger.error(f"{space}   @ blocked service ids: {service_id}")
                    break
        # else:
        #     # Check Next services
        next_service_ids = self._get_next_service_ids(service_id)
        self._logger.debug(f"{space}   L check next service ids: {next_service_ids}")
        for next_service_id in next_service_ids:
            next_depth = depth + 1
            self._set_blocked_nodes(next_service_id, next_depth)

    def _map_template(self, service_id, text_value):
        if not isinstance(text_value, str):
            return text_value
        env = Environment()
        ast = env.parse(text_value)
        ref_keys = meta.find_undeclared_variables(ast)
        value_map = {}
        for ref_key in ref_keys:
            try:
                value_id = f"{service_id}.{ref_key}"
                ref_value = self._datastore.get_input_value(value_id)
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
            env_map = service_info.get('environments')
            if not env_map:
                return {}

            env_params_info = env_map.get('params')
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
            asset_env_map = service_info.get('asset_environments')
            if not asset_env_map:
                return {}

            asset_params_info = asset_env_map.get('params')
            if not asset_params_info:
                return {}

            node_id = service_info.get('node_id')
            asset_params_map = {asset_param_map.get('key'): f"A.{node_id}.{asset_param_map.get('key')}"
                             for asset_param_map in asset_params_info if asset_param_map.get('key')}
            for asset_name, asset_value_id in asset_params_map.items():
                asset_value = self._datastore.get_param_value_service(asset_value_id)
                asset_params_map[asset_name] = self._map_template(service_id, asset_value)
            return asset_params_map
        except Exception as e:
            return {}

    def _extract_forced_param_value(self, service_id, param_name):
        value_id = f"{service_id}.{param_name}"
        extract_param_value = self._datastore.get_output_value(value_id)
        return extract_param_value

    def _extract_param_value(self, service_id, param_map_list) -> dict:
        params = {}
        if not isinstance(param_map_list, list):
            return params

        for param_map in param_map_list:
            param_name = param_map.get('key')
            if 'value' in param_map.keys():
                if param_map.get('refer_type') == 'direct':
                    value_id = f"{service_id}.{param_name}"
                    extract_params_value = self._datastore.get_input_value(value_id)
                else:
                    addr_value = param_map.get('value')
                    extract_params_value = self._datastore.get_output_value(addr_value)
                params[param_name] = extract_params_value
            elif 'values' in param_map.keys():
                value_param_map_list = param_map.get('values')
                sub_service_id = f"{service_id}.{param_name}"
                sub_params = self._extract_param_value(sub_service_id, value_param_map_list)
                params.update({param_name:sub_params})
        return params

    def _get_edge_ids_by_service_id(self, service_id):
        backward_graph = self._meta_pack['backward_graph']
        prev_service_ids = backward_graph.get(service_id)
        edge_params_ids = []
        if not prev_service_ids:
            edge_params_id = f"START-{service_id}"
            edge_params_ids.append(edge_params_id)
        else:
            for prev_service_id in prev_service_ids:
                edge_params_id = f"{prev_service_id}-{service_id}"
                edge_params_ids.append(edge_params_id)
        return edge_params_ids

    def _get_params(self, service_id):
        def get_edge_params(edge_id, edges_param_map):
            param_map_list = edges_param_map.get(edge_id, [])
            params = {}
            if not param_map_list:
                return params
            params = self._extract_param_value(service_id, param_map_list)
            return params

        param_map = {}
        edges_param_map = self._meta_pack['act_edges_param_map']
        edge_ids = self._get_edge_ids_by_service_id(service_id)
        for edge_id in edge_ids:
            param_map = get_edge_params(edge_id, edges_param_map)
        return param_map

    def _get_aggr_params(self, service_id):
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
        aggr_param_map = {}
        if not prev_service_ids:
            return aggr_param_map

        for prev_service_id in prev_service_ids:
            edge_params_id = f"{prev_service_id}-{service_id}"
            param_map = get_edge_params(edge_params_id, edges_param_map)
            param_keys = param_map.keys()
            for param_key in param_keys:
                service_param_map = {
                    prev_service_id: param_map.get(param_key)
                }
                if param_key in aggr_param_map.keys():
                    aggr_param_map[param_key].append(service_param_map)
                else:
                    aggr_param_map[param_key] = [service_param_map]
        return aggr_param_map

    def _get_start_nodes(self):
        start_nodes = self._meta_pack['act_start_nodes']
        return start_nodes

    def _get_end_nodes(self):
        end_nodes = self._meta_pack['act_end_nodes']
        return end_nodes

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

        custom_result_info = self._meta_pack.get('custom_result_meta', {})
        custom_result_meta = custom_result_info.get(service_id)
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

    def _get_task(self, service_id):
        task_map = self._meta_pack.get('act_task_map')
        task_object = task_map.get(service_id)
        return task_object

    def _get_task_state(self, service_id):
        task = self._get_task(service_id)
        task_state = task.get_state()
        return task_state

    def _set_task_state(self, service_id, state):
        task = self._get_task(service_id)
        task.set_state(state)
        self._taskstore.set_state(service_id, state)

    def _set_env_params(self, service_id, params):
        task = self._get_task(service_id)
        task.set_env_params(params)
        self._taskstore.set_env_params(service_id, params)

    def _set_asset_params(self, service_id, params):
        task = self._get_task(service_id)
        task.set_asset_params(params)
        self._taskstore.set_asset_params(service_id, params)

    def _set_params(self, service_id, params):
        task = self._get_task(service_id)
        task.set_params(params)
        self._taskstore.set_params(service_id, params)
        self._datastore.set_service_params_service(service_id, params)

    def _set_result(self, service_id, result):
        task = self._get_task(service_id)
        task.set_result(result)
        self._taskstore.set_result(service_id, result)

    def _set_handler(self, service_id, handler):
        task = self._get_task(service_id)
        task.set_handler(handler)
        self._taskstore.set_handler(service_id, handler)

    def _get_job_result(self, task_map):
        end_service_ids = self._get_end_nodes()
        for end_service_id in end_service_ids:
            end_task = task_map.get(end_service_id)
            result = end_task.get_result()
            return result

    def _check_prev_task_compledted(self, service_id):
        backward_graph = self._meta_pack['backward_graph']
        prev_service_list = backward_graph.get(service_id, [])
        if not prev_service_list:
            return True
        else:
            for prev_service_id in prev_service_list:
                prev_task_state = self._get_task_state(prev_service_id)
                self._logger.debug(f" - Prev_task: {prev_service_id} - {prev_task_state}")
                if prev_task_state not in [TaskState.COMPLETED, TaskState.SKIPPED]:
                    return False
        return True

    def _check_all_completed(self, task_map):
        be_completed = True
        for k, task in task_map.items():
            if task.get_state() not in [TaskState.COMPLETED, TaskState.STOPPED, TaskState.FAILED, TaskState.SKIPPED, TaskState.BLOCKED]:
                be_completed = False
                break
        return be_completed

    def _show_task(self, task_map):
        for service_id, task in task_map.items():
            self._logger.info(f" - [{task.get_state()}] {service_id}")
