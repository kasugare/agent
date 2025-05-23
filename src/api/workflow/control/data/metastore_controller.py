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


    def set_metas(self, wf_comm_meta, wf_nodes_meta, wf_service_pool, wf_edges_meta,
                  wf_edges_grape, wf_prev_edge_grape, wf_resources_meta, start_nodes, end_nodes):
        self._thread_lock.acquire()
        self._cached_metastore_access.set_comm_meta(wf_comm_meta)
        self._cached_metastore_access.set_nodes_meta(wf_nodes_meta)
        self._cached_metastore_access.set_node_service_pool(wf_service_pool)
        self._cached_metastore_access.set_edges_meta(wf_edges_meta)
        self._cached_metastore_access.set_edges_grape_meta(wf_edges_grape)
        self._cached_metastore_access.set_prev_edge_grape_meta(wf_prev_edge_grape)
        self._cached_metastore_access.set_resources_meta(wf_resources_meta)
        self._cached_metastore_access.set_start_nodes_meta(start_nodes)
        self._cached_metastore_access.set_end_nodes_meta(end_nodes)
        self._thread_lock.release()

    def get_metas(self):
        self._thread_lock.acquire()
        meta_pack = {
            "start_nodes": self._cached_metastore_access.get_start_nodes_meta(),
            "end_nodes": self._cached_metastore_access.get_end_nodes_meta(),
            "nodes_info": self._cached_metastore_access.get_nodes_meta(),
            "service_pool": self._cached_metastore_access.get_node_service_pool(),
            "edges_info": self._cached_metastore_access.get_edges_meta(),
            "edges_grape": self._cached_metastore_access.get_edges_grape_meta(),
            "prev_edges_grape": self._cached_metastore_access.get_prev_edges_grpae_meta()
        }
        self._thread_lock.release()
        return meta_pack

    def save_wf_meta_on_file(self, wf_file_meta: Dict, dirpath: str = None, filename: str = None) -> None:
        self._meta_file_access.save_wf_meta_on_file(wf_file_meta, dirpath, filename)

    def load_wf_meta_on_file(self, dirpath: str = None, filename: str = None) -> Dict:
        wf_meta = self._meta_file_access.load_wf_meta_on_file()
        return wf_meta