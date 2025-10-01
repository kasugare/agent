#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.control.meta.edge_transform import EdgeTransformer
from api.workflow.control.meta.env_transform import EnvironmentsTransformer


class MetaParseController:
    def __init__(self, logger):
        self._logger = logger
        self._edge_transformer = EdgeTransformer(logger)
        self._env_transformer = EnvironmentsTransformer(logger)

    def extract_wf_common_info_ctl(self, wf_meta: dict) -> dict:
        wf_metadata = wf_meta.get('metadata')
        wf_comm_meta = {
            'proj_id': wf_metadata.get('project_id'),
            'wf_id': wf_metadata.get('workflow_id'),
            'wf_version': wf_metadata.get('version'),
            'wf_type': wf_metadata.get('type'),
            'wf_name': wf_meta.get('name'),
            'wf_description': wf_meta.get('description'),
        }
        return wf_comm_meta

    def extract_wf_common_env_ctl(self, wf_meta: dict) -> dict:
        wf_common_envs_map = wf_meta.get('environments')
        env_pool = {}
        for env_map in wf_common_envs_map:
            env_code = env_map.get('env_code')
            env_params = env_map.get('env_params')
            for env_param_map in env_params:
                env_id = f"{env_code}.{env_param_map.get('key')}"
                env_pool[env_id] = env_param_map.get('value')
        return env_pool

    def extract_wf_node_env_map_ctl(self, wf_edges_meta: dict) -> dict:
        def extract_node_id(edge_info):
            service_id = edge_info.get('target')
            if service_id == 'None' or service_id == None:
                service_id = edge_info.get('service')
            splited_service_id = service_id.split(".")
            node_id = splited_service_id[0]
            return node_id

        node_env_map_pool = {}
        for edge_id, edge_meta in wf_edges_meta.items():
            node_id = extract_node_id(edge_meta)
            env_info = edge_meta.get('env_info')
            for env_map in env_info:
                try:
                    key = env_map.pop('key')
                    if node_env_map_pool.get(node_id):
                        node_env_map_pool[node_id][key] = env_map
                    else:
                        node_env_map_pool[node_id] = {key: env_map}
                except Exception as e:
                    self._logger.error("not existed node-env parma key")
        return node_env_map_pool

    def extract_wf_to_nodes_ctl(self, wf_meta: dict) -> dict:
        nodes = wf_meta.get('nodes')
        nodes_meta = {node.get('node_id'): node for node in nodes if node.get('node_id')}
        return nodes_meta

    def cvt_wf_to_service_pool_ctl(self, nodes_meta: dict) -> dict:
        service_pool = {}
        add_node_keys = ['node_type', 'role', 'location', 'api_keys',
                         'containable', 'api_info', 'module_info']
        for node_id, node_info in nodes_meta.items():
            services = node_info.get('services')
            for service_name, service_info in services.items():
                node_service_id = f"{node_id}.{service_name}"
                service_info['node_id'] = node_id   # <--
                service_pool[node_service_id] = service_info
                for node_key in add_node_keys:
                    service_pool[node_service_id][node_key] = node_info[node_key]
        return service_pool

    def extract_wf_to_edges_ctl(self, wf_meta: dict, wf_service_pool: dict) -> dict:
        edges_meta = self._edge_transformer.cvt_service_edges(wf_meta, wf_service_pool)
        return edges_meta

    def extract_forward_edge_graph_ctl(self, edges_meta: dict) -> dict:
        forward_edge_graph = dict()
        for edge_id, edge_info in edges_meta.items():
            curr_node = edge_info.get('source')
            next_node = edge_info.get('target')
            param_map_list = edge_info.get('param_info')
            if not forward_edge_graph.get(next_node):
                forward_edge_graph[next_node] = {}
            if curr_node in forward_edge_graph.keys():
                forward_edge_graph[curr_node][next_node] = param_map_list
            else:
                forward_edge_graph[curr_node] = {next_node: param_map_list}
        return forward_edge_graph

    def extract_forward_graph_ctl(self, edges_meta: dict) -> dict:
        forward_graph = dict()
        for edge_id, edge_info in edges_meta.items():
            curr_node = edge_info.get('source')
            next_node = edge_info.get('target')
            if not forward_graph.get(next_node):
                forward_graph[next_node] = []
            if curr_node in forward_graph.keys():
                forward_graph[curr_node].append(next_node)
            else:
                forward_graph[curr_node] = [next_node]
        return forward_graph

    def extract_backward_graph_ctl(self, edges_meta: dict) -> dict:
        backward_edge_graph = dict()
        for edge_id, edge_info in edges_meta.items():
            curr_node = edge_info.get('target')
            prev_node = edge_info.get('source')
            if curr_node in backward_edge_graph.keys():
                backward_edge_graph[curr_node].append(prev_node)
            else:
                backward_edge_graph[curr_node] = [prev_node]
        return backward_edge_graph

    def reverse_forward_graph_ctl(self, forward_edge_graph):
        backward_edge_graph = dict()
        for service_id, target_list in forward_edge_graph.items():
            for forward_service_id in target_list:
                if forward_service_id in backward_edge_graph.keys():
                    backward_edge_graph[forward_service_id].append(service_id)
                else:
                    backward_edge_graph[forward_service_id] = [service_id]
        return backward_edge_graph

    def get_wf_to_resources_ctl(self, wf_meta: dict) -> dict:
        resources = wf_meta.get('resources')
        return resources

    def cvt_wf_to_edge(self, nodes_meta: dict) -> dict:
        edge_map = dict()
        for node_id, node_info in nodes_meta.items():
            next_nodes = node_info['next_nodes']
            edge_map[node_id] = next_nodes
        return edge_map

    def cvt_wf_to_dag(self, wf_meta: dict) -> dict:
        if wf_meta.get('nodes'):
            nodes_meta = wf_meta.get('nodes')
        else:
            nodes_meta = {}

        if wf_meta.get('edges'):
            edges_meta = wf_meta.get('edges')
        else:
            edges_meta = {}

        return wf_meta

    def find_start_nodes_ctl(self, wf_forward_edge_graph: dict) -> list:
        all_nodes = set(wf_forward_edge_graph.keys())
        reachable_nodes = set()
        for node in wf_forward_edge_graph:
            reachable_nodes.update(wf_forward_edge_graph[node])
        start_nodes = all_nodes - reachable_nodes
        return sorted(list(start_nodes))

    def find_end_nodes_ctl(self, wf_backward_edge_graph: dict) -> list:
        end_nodes = self.find_start_nodes_ctl(wf_backward_edge_graph)
        return sorted(list(end_nodes))

    def extract_node_env_value_map_ctl(self, wf_nodes_meta, wf_node_env_map_pool, wf_env_pool) -> dict:
        nodes_env_value_map = self._env_transformer.cvt_node_env_value_map_ctl(wf_nodes_meta, wf_node_env_map_pool, wf_env_pool)
        return nodes_env_value_map

    def extract_custom_result_meta_ctl(self, wf_edges_meta: dict) -> dict:
        custom_result_meta = {}
        for edge_id, edge_meta in wf_edges_meta.items():
            service_id = edge_meta.get('target')
            if not service_id:
                service_id = edge_meta.get('source')
            custom_result_info = edge_meta.get('result_info')
            if custom_result_info:
                custom_result_meta[service_id] = custom_result_info
        return custom_result_meta

    def extract_params_map_ctl(self, start_nodes, wf_service_pool, wf_edges_meta) -> dict:
        edge_params_map = self._edge_transformer.cvt_params_map_ctl(start_nodes, wf_service_pool, wf_edges_meta)
        return edge_params_map
