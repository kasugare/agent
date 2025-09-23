#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.access.meta.meta_file_access import MetaFileAccess
from api.workflow.access.data.cached_metastore_access import CachedMetastoreAccess
from typing import Dict
import threading


class MetastoreController:
    def __init__(self, logger):
        self._logger = logger
        self._thread_lock = threading.Lock()
        self._meta_file_access = MetaFileAccess(logger)
        self._cached_metastore_access = CachedMetastoreAccess(logger)

    def set_metas_ctl(self, wf_comm_meta, wf_nodes_meta, wf_service_pool, wf_edges_meta,
                  wf_forward_edge_graph, wf_backward_edge_graph, wf_resources_meta, start_nodes, end_nodes):
        self.set_comm_meta_ctl(wf_comm_meta)
        self.set_nodes_meta_ctl(wf_nodes_meta)
        self.set_node_service_pool_ctl(wf_service_pool)
        self.set_edges_meta_ctl(wf_edges_meta)
        self.set_forward_graph_meta_ctl(wf_forward_edge_graph)
        self.set_backward_graph_meta_ctl(wf_backward_edge_graph)
        self.set_resources_meta_ctl(wf_resources_meta)
        self.set_start_nodes_meta_ctl(start_nodes)
        self.set_end_nodes_meta_ctl(end_nodes)

    def set_wf_meta_ctl(self, wf_meta):
        self._cached_metastore_access.set_wf_meta_access(wf_meta)

    def get_wf_meta_ctl(self):
        wf_meta = self._cached_metastore_access.get_wf_meta_access()
        return wf_meta

    def set_comm_meta_ctl(self, wf_comm_meta):
        self._cached_metastore_access.set_comm_meta_access(wf_comm_meta)

    def set_nodes_meta_ctl(self, wf_nodes_meta):
        self._cached_metastore_access.set_nodes_meta_access(wf_nodes_meta)

    def set_node_service_pool_ctl(self, wf_service_pool):
        self._cached_metastore_access.set_node_service_pool_access(wf_service_pool)

    def get_node_service_pool_ctl(self):
        service_pool = self._cached_metastore_access.get_node_service_pool_access()
        return service_pool

    def get_start_nodes_meta_ctl(self):
        start_nodes = self._cached_metastore_access.get_start_nodes_meta_access()
        return start_nodes

    def set_edges_meta_ctl(self, wf_edges_meta):
        self._cached_metastore_access.set_edges_meta_access(wf_edges_meta)

    def get_edges_meta_ctl(self):
        wf_edges_meta = self._cached_metastore_access.get_edges_meta_access()
        return wf_edges_meta

    def get_edge_meta_by_edge_id_ctl(self, edge_id):
        wf_edges_meta = self.get_edges_meta_ctl()
        for wf_edge_meta in wf_edges_meta:
            wf_edge_id = wf_edge_meta.get('edge_id')
            if wf_edge_id == edge_id:
                return wf_edge_meta
        return {}

    def set_forward_edge_graph_meta_ctl(self, wf_forward_edge_graph):
        self._cached_metastore_access.set_forward_edge_graph_meta_access(wf_forward_edge_graph)

    def get_forward_edge_graph_meta_ctl(self):
        return self._cached_metastore_access.get_forward_edge_graph_meta_access()

    def set_forward_graph_meta_ctl(self, wf_forward_graph):
        self._cached_metastore_access.set_forward_graph_meta_access(wf_forward_graph)

    def get_forward_graph_meta_ctl(self):
        return self._cached_metastore_access.get_forward_graph_meta_access()

    def set_backward_graph_meta_ctl(self, wf_backward_edge_graph):
        self._cached_metastore_access.set_backward_graph_meta_access(wf_backward_edge_graph)

    def get_backward_graph_meta_ctl(self):
        return self._cached_metastore_access.get_backward_graph_meta_access()

    def set_resources_meta_ctl(self, wf_resources_meta):
        self._cached_metastore_access.set_resources_meta_access(wf_resources_meta)

    def set_start_nodes_meta_ctl(self, start_nodes):
        self._cached_metastore_access.set_start_nodes_meta_access(start_nodes)

    def set_end_nodes_meta_ctl(self, end_nodes):
        self._cached_metastore_access.set_end_nodes_meta_access(end_nodes)

    def set_edges_param_map_ctl(self, service_params_map):
        self._cached_metastore_access.set_edges_param_map_access(service_params_map)

    def get_edges_param_map_ctl(self):
        edges_param_map = self._cached_metastore_access.get_edges_param_map_access()
        return edges_param_map

    def get_metas_ctl(self):
        meta_pack = {
            "start_nodes": self._cached_metastore_access.get_start_nodes_meta_access(),
            "end_nodes": self._cached_metastore_access.get_end_nodes_meta_access(),
            "nodes_info": self._cached_metastore_access.get_nodes_meta_access(),
            "service_pool": self._cached_metastore_access.get_node_service_pool_access(),
            "edges_info": self._cached_metastore_access.get_edges_meta_access(),
            "forward_edge_graph": self._cached_metastore_access.get_forward_edges_graph_meta_access(),
            "forward_graph": self._cached_metastore_access.get_forward_graph_meta_access(),
            "backward_graph": self._cached_metastore_access.get_backward_graph_meta_access(),
            'edges_param_map': self._cached_metastore_access.get_edges_param_map_access()
        }
        return meta_pack

    def save_wf_meta_on_file(self, wf_file_meta: Dict, dirpath: str = None, filename: str = None) -> None:
        self._meta_file_access.save_wf_meta_on_file(wf_file_meta, dirpath, filename)

    def load_wf_meta_on_file(self, dirpath: str = None, filename: str = None) -> Dict:
        wf_meta = self._meta_file_access.load_wf_meta_on_file()
        return wf_meta