#!/usr/bin/env python
# -*- coding: utf-8 -*-
import traceback
from multiprocessing import Queue
from api.serving.executor.api_executor import ApiExecutor
import threading
import asyncio
import time

class NotPreparedPrevJob(Exception):
    def __init__(self):
        super().__init__("Task not done")
        self._errorMessage = "task not done"

    def __str__(self):
        return self._errorMessage


class JobTaskExecutor:
    def __init__(self, logger, meta_pack):
        self._logger = logger
        self._meta_pack = meta_pack
        self._job_status = {}
        self._io_data_pool = {}
        self._job_Q = Queue()
        self._result_set = None

    def _init_job_status(self):
        edges_grape = self._meta_pack.get('edges_grape')
        service_ids = edges_grape.keys()
        job_ids = []
        for service_id, tar_service_id in edges_grape.items():
            job_ids.append(service_id)
            job_ids.extend(tar_service_id)

        job_ids = list(set(job_ids))
        for job_id in job_ids:
            self._set_job_status(job_id)

        print(self._job_status)

    def _set_job_status(self, service_id, status='idle'):
        # 'idle', 'wait', 'running', 'stop', 'done', 'error_pool'
        if service_id in self._job_status.keys():
            self._job_status[service_id]['status'] = status
        else:
            self._job_status[service_id] = {
                'status': status
            }

    def _get_job_status(self, service_id):
        job_info = self._job_status.get(service_id)
        job_status = job_info.get('status')
        return job_status

    def _get_start_nodes(self):
        start_nodes = self._meta_pack['start_nodes']
        return start_nodes

    def _get_node_info(self, service_id):
        node_pool = self._meta_pack.get('service_pool')
        node_info = node_pool.get(service_id)
        return node_info

    def _get_edge_info(self, edge_id):
        edges_info = self._meta_pack.get('edges_info')
        edge_info = edges_info.get(edge_id)
        return edge_info

    def _get_next_nodes(self, curr_node):
        edges_grape = self._meta_pack['edges_grape']
        next_nodes = edges_grape.get(curr_node)
        return next_nodes

    def _get_prev_nodes(self, curr_node):
        prev_edges_grape = self._meta_pack['prev_edges_grape']
        prev_nodes = prev_edges_grape.get(curr_node)
        return prev_nodes

    def _extract_target_params(self, edge_info):
        self._logger.error(edge_info)

    def _combine_params(self, input_params, tar_params_info):
        req_params = tar_params_info.get('input')
        input_node_params = {}
        for req_param_meta in req_params:
            required = req_param_meta.get('required')
            param_name = req_param_meta.get('key')
            data_type = req_param_meta.get('type')
            intput_param_name = input_params.get(param_name)
            if required and not intput_param_name:
                self._logger.error(f"# Not exist required param({param_name} in input_params!")
                continue
            else:
                input_value = input_params.get(param_name)
                input_node_params[param_name] = input_value
        return input_node_params

    def _trans_type_casting(self, value, key_type, value_type):
        key_type = key_type.lower()
        value_type = value_type.lower()

        if key_type in ['str', 'string']:
            if value_type in ['integer', 'int']:
                value = int(value)
            elif value_type in ['double', 'float']:
                value = float(value)
            else:
                value = str(value)
        elif key_type in ['int', 'integer']:
            if value_type in ['integer', 'int']:
                value = int(value)
            elif value_type in ['double', 'float']:
                value = float(value)
            else:
                value = str(value)
        elif key_type in ['list']:
            if value_type in ['list']:
                value = value
            elif value_type in ['str', 'string', 'int']:
                value = [value]
            elif value_type in ['set']:
                value = list(value)
        elif key_type in ['bytes']:
            if value_type in ['str', 'string']:
                value = bytes(value, 'utf-8')
        elif key_type in ['double', 'float']:
            value = float(value)
        elif key_type in ['dict', 'map', 'json']:
            value = dict(value)
        return value

    def _get_input_params(self, key_path):
        pass


    def _get_output_data(self, key_path):
        splited_key_path = key_path.split('.')
        service_id = ".".join(splited_key_path[:2])
        key_name = splited_key_path[-1]
        service_data_meta = self._io_data_pool.get(service_id)
        output_data_map = service_data_meta.get('output')
        if output_data_map:
            output_value = output_data_map.get(key_name)
            return output_value
        return None

    def _gen_next_service_params(self, edge_info):
        def extract_param_name(key_path):
            param_name = key_path.split('.')[-1]
            return param_name
        data_mapper = edge_info.get('data_mapper')

        tar_params = {}
        for param_meta in data_mapper:
            call_method = param_meta.get('call_method')
            key_path = param_meta.get('key')
            value_path = param_meta.get('value')
            src_data_type = param_meta.get('key_type')
            tar_data_type = param_meta.get('value_type')
            param_name = extract_param_name(key_path)

            if call_method.lower() == 'refer':
                try:
                    value = self._get_output_data(value_path)
                    type_casting_value = self._trans_type_casting(value, src_data_type, tar_data_type)
                    tar_params[param_name] = type_casting_value
                except Exception as e:
                    raise NotPreparedPrevJob
            elif call_method.lower() == 'value':
                type_casting_value = self._trans_type_casting(value_path, src_data_type, tar_data_type)
                tar_params[param_name] = type_casting_value
            else:
                pass
        return tar_params

    def _set_node_params(self, service_id, params):
        node_io_data_map = self._io_data_pool.get(service_id)
        if node_io_data_map:
            input_node_data_map = node_io_data_map.get('input')
            if input_node_data_map:
                input_node_data_map.update(params)
            else:
                input_node_data_map = {"intput": params}
            node_io_data_map.update(input_node_data_map)
            self._io_data_pool[service_id] = node_io_data_map
        else:
            node_io_data_map = {"input": params}
            self._io_data_pool[service_id] = node_io_data_map

    def _set_node_result(self, service_id, result):
        node_io_data_map = self._io_data_pool.get(service_id)
        if node_io_data_map:
            output_node_data_map = node_io_data_map.get('output')
            if output_node_data_map:
                output_node_data_map.update(result)
            else:
                output_node_data_map = {"output": result}
            node_io_data_map.update(output_node_data_map)
        else:
            node_io_data_map = {"output": result}
            self._io_data_pool[service_id] = node_io_data_map

    def _get_node_connection_info(self, service_id, node_info):
        splited_service_id = service_id.split(".")
        node_id = splited_service_id[0]
        service_name = splited_service_id[1]

    def _extract_api_info(self, service_id):
        node_info = self._get_node_info(service_id)
        url_info = {
            'url': node_info.get('url'),
            'method': node_info.get('method'),
            'header': node_info.get('header'),
            'body': node_info.get('body')
        }
        return url_info

    def _get_service_role(self, service_id):
        service_pool = self._meta_pack.get('service_pool')
        service_info = service_pool.get(service_id)
        role = service_info.get('role')
        return role

    def _set_init_pararms(self, service_id, request_params):
        node_info = self._get_node_info(service_id)
        self._logger.debug(f" # Step 2. node_info: {node_info}")

        node_type = node_info.get('type')
        if node_type.lower() == 'start_node':
            node_params = node_info.get('params')
            combained_params = self._combine_params(request_params, node_params)
            self._set_job_status(service_id, status='wait')
            self._set_node_params(service_id, combained_params)
            # self._set_node_result(service_id, combained_params)

    def _prepare_next_job(self, service_id, next_service_id):
        def gen_edge_id(curr_node_id, next_node_id):
            edge_id = f"{curr_node_id}-{next_node_id}"
            return edge_id

        edge_id = gen_edge_id(service_id, next_service_id)  ## 공통
        # self._logger.debug(f" # Step 4. edge_id: {edge_id}")

        edge_info = self._get_edge_info(edge_id)  ## 미리 셋팅
        # self._logger.debug(f" # Step 5. edge_info")
        # self._logger.warn(f"    - {edge_info}")
        tar_service_id = edge_info.get('target')

        # self._logger.debug(f" # Step 6. generate target_params") ## 실행시 저장
        tar_params = self._gen_next_service_params(edge_info)
        # self._logger.debug(f"   - {tar_params}")

        # self._logger.debug(f" # Step 7. Save target params") ## 실행시 저장
        self._set_node_params(tar_service_id, tar_params)

        # self._logger.debug(f" # Step 8. get service url info") ## 미리 셋팅
        tar_api_url_info = self._extract_api_info(tar_service_id)
        tar_api_url_info['params'] = tar_params  ## 실행시 셋팅
        # self._logger.debug(f"   - {tar_api_url_info}")

        task_order = self._gen_task_order(tar_service_id, tar_api_url_info, edge_id, edge_info)
        self._logger.debug(f" # Step 9. set task Queue")
        return task_order

    def _gen_task_order(self, service_id, api_url_info, edge_id, edge_info):
        task_order = {
            'service_id': service_id,
            'orders': {
                'endpoint': api_url_info,
                'task_meta': {
                    'edge_id': edge_id,
                    'edge_info': edge_info
                }
            }
        }
        return task_order

    def _request_execution(self, task_order):
        self._job_Q.put_nowait(task_order)

    def _run_executor(self, task_order):
        self._logger.debug(f" # Step 10. Call API")
        # self._logger.info(task_map)
        order_sheet = task_order.get('orders')
        service_id = task_order.get('service_id')
        end_point = order_sheet.get('endpoint')
        task_meta = order_sheet.get('task_meta')
        edge_id = task_meta.get('edge_id')
        edge_info = task_meta.get('edge_info')

        self._set_job_status(service_id, status='running')

        executor = ApiExecutor(self._logger)
        output_result = executor.run_api(end_point)
        result = output_result.get('result')
        self._logger.warn(f"  RUN: < edge_id: {edge_id} >")
        self._logger.warn(f"  RUN: service_id: {service_id}")
        self._logger.warn(f"  RUN: end_point: {end_point}")
        self._set_job_status(service_id, status='done')
        task_order['output'] = result

        self._job_Q.put_nowait(task_order)

    def _check_runnable(self, service_id):
        def gen_edge_id(curr_node_id, next_node_id):
            edge_id = f"{curr_node_id}-{next_node_id}"
            return edge_id

        next_service_ids = self._get_next_nodes(service_id)
        try:
            for next_service_id in next_service_ids:
                print(f" - 1: {next_service_id}")
                edge_id = gen_edge_id(service_id, next_service_id)  ## 공통
                print(f" - 2: {edge_id}")
                edge_info = self._get_edge_info(edge_id)  ## 미리 셋팅
                print(f" - 3: {edge_info}")
                self._gen_next_service_params(edge_info)
                print(f" - 4: gen next_service")
            return True
        except Exception as e:
            self._logger.error(e)
            return False

    def _check_finished_prev_services(self, service_id):
        prev_edges_grape = self._meta_pack.get('prev_edges_grape')
        for prev_service_id in prev_edges_grape.get(service_id):
            status = self._get_job_status(prev_service_id)
            if status is not 'done':
                return False
        return True

    def _check_finished_all_job(self):
        for service_id, status_map in self._job_status.items():
            status = status_map.get('status')
            if status is not 'done':
                return False
        return True


    def _task_handler(self):
        def start_job(task_map):
            thread = threading.Thread(target=self._run_executor, args=(task_map,))
            thread.start()

        while True:
            task_order = self._job_Q.get()
            service_id = task_order.get('service_id')
            status = self._get_job_status(service_id)

            if status == 'idle':
                self._logger.error(f"[IDLE --> WAIT] - {service_id}")
                self._set_job_status(service_id, status='wait')
                is_finished_prev = self._check_finished_prev_services(service_id)
                if is_finished_prev:
                    self._request_execution(task_order)
            elif status == 'wait':
                self._logger.error(f"[WAIT --> RUNNING] - {service_id}")
                role = self._get_service_role(service_id)
                if role.lower() == 'start':
                    end_pool = self._io_data_pool.get(service_id)
                    task_order['output'] = end_pool.get('input')
                    self._set_job_status(service_id, status='done')
                    self._job_Q.put_nowait(task_order)
                elif role == 'end':
                    end_pool = self._io_data_pool.get(service_id)
                    task_order['output'] = end_pool.get('input')
                    self._result_set = end_pool.get('intput')
                    self._set_job_status(service_id, status='done')
                    self._job_Q.put_nowait(task_order)
                elif role == 'aggregation':
                    start_job(task_order)
                else:
                    start_job(task_order)
            elif status == 'running':
                pass
            elif status == 'done':
                self._logger.error(f"[RUNNING --> DONE] - {service_id}")
                result = task_order.get('output')
                self._logger.error(f" - {service_id} : {result}")

                self._set_node_result(service_id, result)
                next_service_ids = self._get_next_nodes(service_id)
                if not next_service_ids:
                    self._print_data_pool()
                    continue
                for next_service_id in next_service_ids:
                    self._logger.error(f"[DONE --> NEXT] - {service_id} : {next_service_id}")
                    is_finished_prev = self._check_finished_prev_services(next_service_id)
                    if is_finished_prev:
                        task_order = self._prepare_next_job(service_id, next_service_id)
                        self._request_execution(task_order)

            print("-" * 200)
            self._print_job_status()
            print("-" * 200)
            self._print_data_pool()
            print("-" * 200)
            is_job_finish = self._check_finished_all_job()
            # if is_job_finish:
            #     break
        print("DONE DONE DONE")
        return self._result_set

    def _print_data_pool(self):
        self._logger.info("#######################")
        self._logger.info("#   Service IO Data   #")
        self._logger.info("#######################")
        for k , v in self._io_data_pool.items():
            self._logger.info(f" <{k}>")
            iv = v.get('input')
            if iv:
                self._logger.info(f"    - input : {iv}")
            ov = v.get('output')
            if ov:
                self._logger.info(f"    - output : {ov}")

    def _print_job_status(self):
        self._logger.info("#######################")
        self._logger.info("#     Job Status      #")
        self._logger.info("#######################")
        for k, v in self._job_status.items():
            self._logger.info(f" - {k} : {v}")

    def do_process(self, request_params):
        self._logger.critical(f" # user params: {request_params}")
        self._init_job_status()
        start_nodes = self._get_start_nodes()
        for service_id in start_nodes:
            self._logger.debug(f" # Step 1. service_id: {service_id}")
            self._set_init_pararms(service_id, request_params)
            task_order = self._gen_task_order(service_id, None, None, None)
            self._set_job_status(service_id, status='wait')
            self._request_execution(task_order)

        # result = self._task_handler()
        thread = threading.Thread(target=self._task_handler, args=())
        thread.start()
        print(self._result_set)
        return self._result_set