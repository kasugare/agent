#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.conf_system import getRecipeDir, getRecipeFile, isMetaAutoLoad
from api.workflow.service.data.meta_store_service import MetaStoreService
from api.workflow.control.meta.meta_parse_controller import MetaParseController
from typing import Dict, List, Any
from watchfiles import awatch
import traceback
import threading
import asyncio
import time
import os


class WorkflowMetaParser:
    def __init__(self, logger):
        self._logger = logger
        self._metastore = MetaStoreService(logger)
        self._meta_controller = MetaParseController(logger)

    def _gen_dag_file_path(self, wf_meta, request_id):
        if not request_id:
            request_id = format(int(time.time() * 100000), "X")
        wf_comm_meta = self.extract_wf_common_info_service(wf_meta)
        proj_id = wf_comm_meta.get('proj_id')
        wf_id = wf_comm_meta.get('wf_id')
        dirpath = os.path.join(getRecipeDir(), proj_id)
        filename = f"{int(time.time()*1000)}-{wf_id}-{request_id}.json"
        return dirpath, filename

    def set_meta(self, wf_meta: Dict, request_id: str=None) -> None:
        dirpath, filename = self._gen_dag_file_path(wf_meta, request_id)
        self._metastore.set_wf_meta_file_service(wf_meta, dirpath=dirpath, filename=filename)
        self._metastore.set_wf_meta_service(wf_meta)
        self.parse_wf_meta(wf_meta)

    def change_wf_meta(self, updated_wf_meta: Dict, request_id: str=None) -> None:
        current_wf_meta = self._metastore.get_wf_meta_service()
        if current_wf_meta != updated_wf_meta:
            self._logger.debug("# New Meta Update")
            dirpath, filename = self._gen_dag_file_path(updated_wf_meta, request_id)
            self._metastore.clear()
            self._metastore.set_wf_meta_file_service(updated_wf_meta, dirpath=dirpath, filename=filename)
            self._metastore.set_wf_meta_service(updated_wf_meta)
            self.parse_wf_meta(updated_wf_meta)
        else:
            self._metastore.clear()
            self._metastore.set_wf_meta_service(updated_wf_meta)
            self.parse_wf_meta(updated_wf_meta)

    def extract_wf_id(self, wf_meta: Dict) -> str:
        wf_comm_meta = self._meta_controller.extract_wf_common_info_ctl(wf_meta)
        wf_id = wf_comm_meta.get('wf_id')
        return wf_id

    def extract_wf_common_info_service(self, wf_meta: Dict) -> Dict:
        wf_comm_meta = self._meta_controller.extract_wf_common_info_ctl(wf_meta)
        return wf_comm_meta

    def extract_wf_common_env_service(self, wf_meta: Dict) -> Dict:
        wf_env_pool = self._meta_controller.extract_wf_common_env_ctl(wf_meta)
        return wf_env_pool

    def extract_wf_node_env_service(self, wf_edges_meta: Dict) -> Dict:
        wf_node_env_map_pool = self._meta_controller.extract_wf_node_env_map_ctl(wf_edges_meta)
        return wf_node_env_map_pool

    def extract_wf_node_asset_service(self, wf_edges_meta: Dict) -> Dict:
        node_asset_map_pool = self._meta_controller.extract_wf_node_asset_map_ctl(wf_edges_meta)
        return node_asset_map_pool

    def extract_wf_to_nodes_service(self, wf_meta: Dict) -> Dict:
        wf_nodes_meta = self._meta_controller.extract_wf_to_nodes_ctl(wf_meta)
        return wf_nodes_meta

    def cvt_wf_to_service_pool_service(self, wf_nodes_meta: Dict) -> Dict:
        wf_service_pool = self._meta_controller.cvt_wf_to_service_pool_ctl(wf_nodes_meta)
        return wf_service_pool

    def extract_wf_to_edges_service(self, wf_meta, wf_service_pool: Dict) -> Dict:
        wf_edges_meta = self._meta_controller.extract_wf_to_edges_ctl(wf_meta, wf_service_pool)
        return wf_edges_meta

    def extract_forward_edge_graph_service(self, wf_edges_meta:Dict) -> Dict:
        wf_forward_edge_graph = self._meta_controller.extract_forward_edge_graph_ctl(wf_edges_meta)
        return wf_forward_edge_graph

    def extract_forward_graph_service(self, wf_edges_meta: Dict) -> Dict:
        wf_forward_graph = self._meta_controller.extract_forward_graph_ctl(wf_edges_meta)
        return wf_forward_graph

    def extract_backward_graph_service(self, wf_edges_meta: Dict) -> Dict:
        wf_backward_graph = self._meta_controller.extract_backward_graph_ctl(wf_edges_meta)
        return wf_backward_graph

    def reverse_forward_graph_service(self, wf_forward_graph) -> Dict:
        wf_backward_graph = self._meta_controller.reverse_forward_graph_ctl(wf_forward_graph)
        return wf_backward_graph

    def get_wf_to_resources_service(self, wf_meta: Dict) -> Dict:
        wf_resources_meta = self._meta_controller.get_wf_to_resources_ctl(wf_meta)
        return wf_resources_meta

    def find_start_nodes_service(self, wf_forward_graph: Dict) -> List:
        start_nodes = self._meta_controller.find_start_nodes_ctl(wf_forward_graph)
        return start_nodes

    def find_end_nodes_service(self, wf_backward_graph: Dict) -> List:
        end_nodes = self._meta_controller.find_end_nodes_ctl(wf_backward_graph)
        return end_nodes

    def extract_node_environments_value_map_service(self, wf_nodes_meta, wf_node_env_map_pool, wf_env_pool) -> Dict:
        nodes_env_value_map = self._meta_controller.extract_node_env_value_map_ctl(wf_nodes_meta, wf_node_env_map_pool, wf_env_pool)
        return nodes_env_value_map

    def extract_node_asset_value_map_service(self, wf_nodes_meta, wf_node_asset_map_pool, wf_env_pool) -> Dict:
        nodes_env_value_map = self._meta_controller.extract_node_asset_value_map_ctl(wf_nodes_meta, wf_node_asset_map_pool, wf_env_pool)
        return nodes_env_value_map

    def extract_custom_result_meta_service(self, wf_edges_meta: Dict) -> Dict:
        custom_result_meta = self._meta_controller.extract_custom_result_meta_ctl(wf_edges_meta)
        return custom_result_meta

    def extract_params_map_service(self, start_nodes, wf_service_pool, wf_edges_meta) -> Dict:
        edge_params_map = self._meta_controller.extract_params_map_ctl(start_nodes, wf_service_pool, wf_edges_meta)
        return edge_params_map

    def parse_wf_meta(self, wf_meta: Dict, metastore):
        try:
            if not wf_meta:
                wf_meta = self._metastore.get_wf_meta_file_service()
                return

            self._logger.info("# [DAG Loader] Step 01. Extract Common Info")
            wf_comm_meta = self.extract_wf_common_info_service(wf_meta)
            # self._print_debug_data(wf_comm_meta)

            self._logger.info("# [DAG Loader] Step 02. Extract Resource Meta")
            wf_resources_meta = self.get_wf_to_resources_service(wf_meta)
            # self._print_debug_data(wf_resources_meta)

            self._logger.info("# [DAG Loader] Step 03. Extract Nodes")
            wf_nodes_meta = self.extract_wf_to_nodes_service(wf_meta)
            # self._print_debug_data(wf_nodes_meta)

            self._logger.info("# [DAG Loader] Step 04. Extract common environment params")
            wf_env_pool = self.extract_wf_common_env_service(wf_meta)
            # self._print_debug_data(wf_env_pool)

            self._logger.info("# [DAG Loader] Step 05. Extract Service Pool")
            wf_service_pool = self.cvt_wf_to_service_pool_service(wf_nodes_meta)
            # self._print_debug_data(wf_service_pool)

            self._logger.info("# [DAG Loader] Step 06. Extract Edges")
            wf_edges_meta = self.extract_wf_to_edges_service(wf_meta, wf_service_pool) # Meta & DataIO
            # self._print_debug_data(wf_edges_meta)

            self._logger.info("# [DAG Loader] Step 07. Extract environment values") # DataIO
            wf_node_env_map_pool = self.extract_wf_node_env_service(wf_edges_meta)
            nodes_env_value_map = self.extract_node_environments_value_map_service(wf_nodes_meta, wf_node_env_map_pool, wf_env_pool)
            self._print_debug_data(nodes_env_value_map)

            self._logger.info("# [DAG Loader] Step 08. Extract asset values") # DataIO
            node_asset_map_pool = self.extract_wf_node_asset_service(wf_edges_meta)
            nodes_asset_value_map = self.extract_node_asset_value_map_service(wf_nodes_meta, node_asset_map_pool, wf_env_pool)  # DataIO
            self._print_debug_data(nodes_asset_value_map)

            self._logger.info("# [DAG Loader] Step 09. Extract node's customized result set")
            custom_result_meta = self.extract_custom_result_meta_service(wf_edges_meta)
            self._print_debug_data(custom_result_meta)

            self._logger.info("# [DAG Loader] Step 10. Extract Forward-Edge graph")
            wf_forward_edge_graph = self.extract_forward_edge_graph_service(wf_edges_meta)
            self._print_debug_data(wf_forward_edge_graph)

            self._logger.info("# [DAG Loader] Step 11. Extract Forward-graph")
            wf_forward_graph = self.extract_forward_graph_service(wf_edges_meta)
            self._print_debug_data(wf_forward_graph)

            self._logger.info("# [DAG Loader] Step 12. Extract backward-graph")
            wf_backward_graph = self.extract_backward_graph_service(wf_edges_meta)
            self._print_debug_data(wf_backward_graph)

            self._logger.info("# [DAG Loader] Step 13. Extract Start Node from forward_graph")
            start_nodes = self.find_start_nodes_service(wf_forward_graph)
            self._print_debug_data(start_nodes)

            self._logger.info("# [DAG Loader] Step 14. Extract End Node from backward_graph")
            end_nodes = self.find_end_nodes_service(wf_backward_graph)
            self._print_debug_data(end_nodes)

            self._logger.info("# [DAG Loader] Step 15. Extract service params-map")
            edges_param_map = self.extract_params_map_service(start_nodes, wf_service_pool, wf_edges_meta)
            self._print_debug_data(edges_param_map)

            self._metastore.set_comm_meta_service(wf_comm_meta) # metastore
            self._metastore.set_env_pool_service(wf_env_pool) # metastore
            self._metastore.set_resources_meta_service(wf_resources_meta) # metastore
            self._metastore.set_nodes_meta_service(wf_nodes_meta) # metastore
            self._metastore.set_node_service_pool_service(wf_service_pool) # metastore
            self._metastore.set_edges_meta_service(wf_edges_meta) # metastore

            self._metastore.set_nodes_env_value_map_service(nodes_env_value_map) # metastore
            self._metastore.set_nodes_asset_value_map_service(nodes_env_value_map)  # metastore

            self._metastore.set_custom_result_meta_service(custom_result_meta) # metastore
            self._metastore.set_forward_edge_graph_meta_service(wf_forward_edge_graph) # metastore
            self._metastore.set_forward_graph_meta_service(wf_forward_graph) # metastore
            self._metastore.set_backward_graph_meta_service(wf_backward_graph) # metastore
            self._metastore.set_start_nodes_meta_service(start_nodes) # metastore
            self._metastore.set_end_nodes_meta_service(end_nodes) # metastore
            self._metastore.set_edges_param_map_service(edges_param_map) # metastore

            # self._metastore.set_init_service_params_service(wf_edges_meta) # dataio - meta_pack: edges_info
            # self._metastore.set_init_nodes_env_params_service(nodes_env_value_map) # dataio
            # self._metastore.set_init_nodes_asset_params_service(nodes_asset_value_map) # dataio

        except Exception as e:
            self._logger.error("Wrong workflow meta")
            raise

    def get_metastore(self):
        return self._metastore

    def get_meta_pack(self):
        meta_pack = self._metastore.get_meta_pack_service()
        return meta_pack

    def _print_task_map(self, task_map, edges_param_map):
        for service_id, task in task_map.items():
            self._logger.debug(f" - {service_id}")
            self._logger.debug(f"         - {task.get_state()}")

    def _print_debug_data(self, debug_data) -> None:
        if isinstance(debug_data, dict):
            for k, v in debug_data.items():
                self._logger.debug(f"  - {k} : {v}")
        elif isinstance(debug_data, list):
            for l in debug_data:
                self._logger.debug(f"  - {l}")
        else:
            self._logger.debug(f"  - {debug_data}")
