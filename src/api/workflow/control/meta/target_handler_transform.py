#!/usr/bin/env python
# -*- coding: utf-8 -*-


class TargetHandlerTransformer:
    def __init__(self, logger):
        self._logger = logger


    def extract_references(self, wf_nodes_meta, wf_edges_meta):
        self.extract_required_nodes_info(wf_nodes_meta, wf_edges_meta)
        # print(wf_nodes_meta)
        # print("-"* 100)
        # print(wf_edges_meta)
        # for edge_id, edge_map in wf_edges_meta.items():
        #     print(edge_id)
        #     print(edge_map)
        #     tar_handler = edge_map.get('target_handler')
        #     ref_nodes_info = tar_handler.get('references')
        #     if not ref_nodes_info:
        #         continue
        #
        #     for ref_node_map in ref_nodes_info:
        #         node_id = ref_node_map.get("node_id")
        #         node_meta = wf_nodes_meta.get(node_id)
        #         print(f" - {node_meta}")
        #         api_info = node_meta.get('api_info')
        #         url = api_info.get('url')

    def _find_required_node_ids(self, node_id, refer_key, wf_edges_meta):
        node_ids = []
        for edge_id, edge_meta in wf_edges_meta.items():
            service_id = edge_meta.get('target')
            if node_id != service_id.split(".")[0]:
                continue
            target_handler = edge_meta.get('target_handler', {})
            references = target_handler.get('references', [])
            for required_node_info in references:
                if refer_key == required_node_info.get("refer_key", ""):
                    req_node_id = required_node_info.get("node_id")
                    node_ids.append(req_node_id)
        return node_ids

    def _get_node_url(self, req_node_id, wf_nodes_meta):
        node_meta = wf_nodes_meta.get(req_node_id)
        api_info = node_meta.get('api_info')
        url = api_info.get('base_url')

    def extract_required_nodes_info(self, wf_nodes_meta, wf_edges_meta):
        for node_id, node_info in wf_nodes_meta.items():
            required_nodes = node_info.get('required_nodes')
            for required_map in required_nodes:
                refer_key = required_map.get('reference_key')
                required_nodes = self._find_required_node_ids(node_id, refer_key, wf_edges_meta)
                for req_node_id in required_nodes:
                    node_meta = wf_nodes_meta.get(req_node_id)
                    api_info = node_meta.get('api_info')
                    base_url = api_info.get('base_url')
                    print(node_id, refer_key, base_url)







