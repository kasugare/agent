#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.protocol.protocol_message import gen_task_order


class WorkflowNavigator:
    def __init__(self, logger, data_service):
        self._logger = logger
        self._data_service = data_service
        self._meta_pack = self.get_meta_pack()

        self._job_status = {}
        self._result_set = None

    def init_job_status(self):
        edges_grape = self._meta_pack.get('edges_grape')
        job_ids = []
        for service_id, tar_service_id in edges_grape.items():
            job_ids.append(service_id)
            job_ids.extend(tar_service_id)

        job_ids = list(set(job_ids))
        for job_id in job_ids:
            self.set_job_status(job_id)

        print(self._job_status)

    def check_finished_all_job(self):
        for service_id, status_map in self._job_status.items():
            status = status_map.get('status')
            if status is not 'done':
                return False
        return True

    def set_job_status(self, service_id, status='idle'):
        """ status = 'idle', 'wait', 'running', 'stop', 'done', 'error_pool' """
        if service_id in self._job_status.keys():
            self._job_status[service_id]['status'] = status
        else:
            self._job_status[service_id] = {
                'status': status
            }

    def get_job_status(self, service_id):
        job_info = self._job_status.get(service_id)
        job_status = job_info.get('status')
        return job_status

    def get_meta_pack(self):
        meta_pack = self._data_service.get_meta_pack()
        return meta_pack

    def get_start_nodes(self):
        start_nodes = self._meta_pack['start_nodes']
        return start_nodes

    def get_node_info(self, service_id):
        node_pool = self._meta_pack.get('service_pool')
        node_info = node_pool.get(service_id)
        return node_info

    def get_edge_info(self, edge_id):
        edges_info = self._meta_pack.get('edges_info')
        edge_info = edges_info.get(edge_id)
        return edge_info

    def get_next_nodes(self, curr_node):
        edges_grape = self._meta_pack['edges_grape']
        next_nodes = edges_grape.get(curr_node)
        return next_nodes

    def get_prev_nodes(self, curr_node):
        prev_edges_grape = self._meta_pack['prev_edges_grape']
        prev_nodes = prev_edges_grape.get(curr_node)
        return prev_nodes

    # Deprecated
    def prepare_next_job(self, service_id, next_service_id):
        def gen_edge_id(curr_node_id, next_node_id):
            edge_id = f"{curr_node_id}-{next_node_id}"
            return edge_id

        edge_id = gen_edge_id(service_id, next_service_id)  ## 공통
        # self._logger.debug(f" # Step 4. edge_id: {edge_id}")

        edge_info = self.get_edge_info(edge_id)  ## 미리 셋팅
        # self._logger.debug(f" # Step 5. edge_info")
        # self._logger.warn(f"    - {edge_info}")
        tar_service_id = edge_info.get('target')

        # self._logger.debug(f" # Step 6. generate target_params") ## 실행시 저장
        tar_params = self._data_service.get_next_service_params(edge_info)
        # self._logger.debug(f"   - {tar_params}")

        # self._logger.debug(f" # Step 7. Save target params") ## 실행시 저장
        self._data_service.set_service_params(tar_service_id, tar_params)

        # self._logger.debug(f" # Step 8. get service url info") ## 미리 셋팅
        tar_api_url_info = self.extract_api_info(tar_service_id)
        tar_api_url_info['params'] = tar_params  ## 실행시 셋팅
        # self._logger.debug(f"   - {tar_api_url_info}")

        task_order = gen_task_order(None, tar_service_id, edge_id, tar_api_url_info, edge_info)
        self._logger.debug(f" # Step 9. set task Queue")
        return task_order

    # Deprecated
    def set_init_params(self, service_id, request_params):
        def compose_node_params(input_params, tar_params_info):
            req_params = tar_params_info.get('helloworld')
            input_node_params = {}
            for req_param_meta in req_params:
                required = req_param_meta.get('required')
                param_name = req_param_meta.get('key')
                intput_param_name = input_params.get(param_name)
                if required and not intput_param_name:
                    self._logger.error(f"# Not exist required param({param_name} in input_params!")
                    continue
                else:
                    input_value = input_params.get(param_name)
                    input_node_params[param_name] = input_value
            return input_node_params

        node_info = self.get_node_info(service_id)
        self._logger.debug(f" # Step 2. node_info: {node_info}")

        node_type = node_info.get('type')
        if node_type.lower() == 'start_node':
            node_params = node_info.get('params')
            params_map = compose_node_params(request_params, node_params)
            self.set_job_status(service_id, status='wait')
            self._data_service.set_service_params(service_id, params_map)
            self._data_service.set_service_result(service_id, params_map)

    def extract_api_info(self, service_id):
        node_info = self.get_node_info(service_id)
        url_info = {
            'url': node_info.get('url'),
            'method': node_info.get('method'),
            'header': node_info.get('header'),
            'body': node_info.get('body')
        }
        return url_info

    def get_service_role(self, service_id):
        service_pool = self._meta_pack.get('service_pool')
        service_info = service_pool.get(service_id)
        role = service_info.get('role')
        return role

    def check_runnable(self, service_id):
        def gen_edge_id(curr_node_id, next_node_id):
            edge_id = f"{curr_node_id}-{next_node_id}"
            return edge_id

        next_service_ids = self.get_next_nodes(service_id)
        try:
            for next_service_id in next_service_ids:
                print(f" - 1: {next_service_id}")
                edge_id = gen_edge_id(service_id, next_service_id)  ## 공통
                print(f" - 2: {edge_id}")
                edge_info = self.get_edge_info(edge_id)  ## 미리 셋팅
                print(f" - 3: {edge_info}")
                self._data_service.get_next_service_params(edge_info)
                print(f" - 4: gen next_service")
            return True
        except Exception as e:
            self._logger.error(e)
            return False

    def check_finished_prev_services(self, service_id):
        prev_edges_grape = self._meta_pack.get('prev_edges_grape')
        for prev_service_id in prev_edges_grape.get(service_id):
            status = self.get_job_status(prev_service_id)
            if status is not 'done':
                return False
        return True

    def print_service(self):
        print("-" * 200)
        self.print_job_status()
        print("-" * 200)
        self.print_data_pool()
        print("-" * 200)

    def print_data_pool(self):
        self._logger.info("#######################")
        self._logger.info("#   Service IO Data   #")
        self._logger.info("#######################")
        data_pool = self._data_service.get_service_data_pool()
        for k , v in data_pool.items():
            self._logger.info(f" <{k}>")
            iv = v.get('helloworld')
            if iv:
                self._logger.info(f"    - helloworld : {iv}")
            ov = v.get('output')
            if ov:
                self._logger.info(f"    - output : {ov}")

    def print_job_status(self):
        self._logger.info("#######################")
        self._logger.info("#     Job Status      #")
        self._logger.info("#######################")
        for k, v in self._job_status.items():
            self._logger.info(f" - {k} : {v}")