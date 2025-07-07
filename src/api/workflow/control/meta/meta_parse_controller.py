#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.control.meta.edge_transform import EdgeTransformer

class MetaParseController:
    def __init__(self, logger):
        self._logger = logger
        self._edge_transformer = EdgeTransformer(logger)

    def extract_wf_common_info(self, wf_meta: dict) -> dict:
        wf_comm_meta = {
            'wf_id': wf_meta.get('workflow_id'),
            'wf_name': wf_meta.get('name'),
            'wf_version': wf_meta.get('version'),
            'wf_description': wf_meta.get('description'),
            'run_type': wf_meta.get('run_mode')
        }
        return wf_comm_meta

    def extract_wf_to_nodes(self, wf_meta: dict) -> dict:
        nodes = wf_meta.get('nodes')
        nodes_meta = {node.get('node_id'): node for node in nodes if node.get('node_id')}
        return nodes_meta

    def cvt_wf_to_service_pool(self, nodes_meta: dict) -> dict:
        service_pool = {}
        add_node_keys = ['node_type', 'role', 'location', 'api_keys', 'containable']
        for node_id, node_info in nodes_meta.items():
            services = node_info.get('services')
            for service_name, service_info in services.items():
                node_service_id = f"{node_id}.{service_name}"
                service_pool[node_service_id] = service_info
                for node_key in add_node_keys:
                    service_pool[node_service_id][node_key] = node_info[node_key]
        return service_pool

    def extract_wf_to_edges(self, wf_meta: dict, wf_service_pool: dict) -> dict:
        edges_meta = self._edge_transformer.cvt_service_edges(wf_meta, wf_service_pool)
        return edges_meta

    def extract_forward_edge_to_graph(self, edges_meta: dict) -> dict:
        forward_edge_graph = dict()
        for edge_id, edge_info in edges_meta.items():
            curr_node = edge_info.get('source')
            next_node = edge_info.get('target')
            if curr_node in forward_edge_graph.keys():
                forward_edge_graph[curr_node].append(next_node)
            else:
                forward_edge_graph[curr_node] = [next_node]
        return forward_edge_graph

    def extract_reverse_edge_graph(self, edges_meta: dict) -> dict:
        reverse_edge_graph = dict()
        for edge_id, edge_info in edges_meta.items():
            curr_node = edge_info.get('target')
            prev_node = edge_info.get('source')
            if curr_node in reverse_edge_graph.keys():
                reverse_edge_graph[curr_node].append(prev_node)
            else:
                reverse_edge_graph[curr_node] = [prev_node]
        return reverse_edge_graph

    def get_wf_to_resources(self, wf_meta: dict) -> dict:
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

    def find_start_nodes(self, wf_forward_edge_graph: dict) -> list:
        all_nodes = set(wf_forward_edge_graph.keys())
        reachable_nodes = set()
        for node in wf_forward_edge_graph:
            reachable_nodes.update(wf_forward_edge_graph[node])
        start_nodes = all_nodes - reachable_nodes
        return sorted(list(start_nodes))

    def find_end_nodes(self, wf_reverse_edge_graph: dict) -> list:
        end_nodes = self.find_start_nodes(wf_reverse_edge_graph)
        return sorted(list(end_nodes))