#!/usr/bin/env python
# -*- coding: utf-8 -*-

class JobTaskExecutor:
    def __init__(self, logger, meta_pack):
        self._logger = logger
        self._meta_pack = meta_pack
        self._io_data_pool = {}

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
            # self._logger.debug(f"  - ({required}) {param_name}: {data_type} ")
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
        elif key_type in ['dict', 'map']:
            pass
        elif key_type in ['json']:
            pass
        return value

    def _get_output_data(self, key_path):
        splited_key_path = key_path.split('.')
        service_id = ".".join(splited_key_path[:2])
        key_name = splited_key_path[-1]
        service_data_meta = self._io_data_pool.get(service_id)
        output_data_map = service_data_meta.get('output')
        output_value = output_data_map.get(key_name)
        return output_value


    def _gen_next_node_params(self, edge_info):
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
                value = self._get_output_data(value_path)
                type_casting_value = self._trans_type_casting(value, src_data_type, tar_data_type)
                tar_params[param_name] = type_casting_value
            elif call_method.lower() == 'value':
                type_casting_value = self._trans_type_casting(value_path, src_data_type, tar_data_type)
                tar_params[param_name] = type_casting_value
            else:
                pass
        return tar_params


    def _set_node_params(self, node_id, params):
        node_io_data_map = self._io_data_pool.get(node_id)
        if node_io_data_map:
            input_node_data_map = node_io_data_map.get('input')
            if input_node_data_map:
                input_node_data_map.update(params)
            else:
                input_node_data_map = {"intput": params}
            node_io_data_map.update(input_node_data_map)
            self._io_data_pool[node_id] = node_io_data_map
        else:
            node_io_data_map = {"input": params}
            self._io_data_pool[node_id] = node_io_data_map

    def _set_node_result(self, node_id, result):
        node_io_data_map = self._io_data_pool.get(node_id)
        if node_io_data_map:
            output_node_data_map = node_io_data_map.get('output')
            if output_node_data_map:
                output_node_data_map.update(result)
            else:
                output_node_data_map = {"output": result}
            node_io_data_map.update(output_node_data_map)
        else:
            node_io_data_map = {"output": result}
            self._io_data_pool[node_id] = node_io_data_map
        print(node_io_data_map)

    def _prepare_execution(self, request_params, service_id):
        def gen_edge_id(curr_node_id, next_node_id):
            edge_id = f"{curr_node_id}-{next_node_id}"
            return edge_id

        node_info = self._get_node_info(service_id)
        self._logger.debug(f" # Step 2: node_info: {node_info}")

        node_type = node_info.get('type')
        if node_type.lower() == 'start_node':
            node_params = node_info.get('params')
            combained_params = self._combine_params(request_params, node_params)
            self._set_node_params(service_id, combained_params)
            self._set_node_result(service_id, combained_params)

        next_node_ids = self._get_next_nodes(service_id)
        self._logger.debug(f" # Step 3: next_nodes: {next_node_ids}")
        for next_node_id in next_node_ids:
            edge_id = gen_edge_id(service_id, next_node_id)
            self._logger.debug(f" # Step 4: edge_id: {edge_id}")

            edge_info = self._get_edge_info(edge_id)
            self._logger.debug(f" # Step 5: edge_info")
            self._logger.warn(f"    - {edge_info}")

            self._logger.debug(f" # Step 6: generate target_params")
            tar_params = self._gen_next_node_params(edge_info)
            self._logger.debug(f"   - {tar_params}")

            self._logger.debug(f" # Step 7: Save target params")
            tar_node_id = edge_info.get('target')
            self._set_node_params(tar_node_id, tar_params)

            self._logger.debug(f" # Step 8: get service node info")

        self._print_data_pool()

    def _print_data_pool(self):
        for k , v in self._io_data_pool.items():
            self._logger.debug(f" <{k}>")
            iv = v.get('input')
            if iv:
                self._logger.debug(f"    - input : {iv}")
            ov = v.get('output')
            if ov:
                self._logger.debug(f"    - output : {ov}")

    def do_process(self, request_params):
        self._logger.critical(f" # user params: {request_params}")
        start_nodes = self._get_start_nodes()
        for service_id in start_nodes:
            self._logger.debug(f" # Step 1: service_id: {service_id}")
            self._prepare_execution(request_params, service_id)
