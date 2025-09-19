#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 통짜 복사

from common.conf_system import getRecipeDir, getRecipeFile
from api.workflow.control.meta.meta_parse_controller import MetaParseController
from typing import Dict, List, Any
from watchfiles import awatch
import traceback
import threading
import asyncio
import os


class MetaLoadService:
    def __init__(self, logger, datastore): # <--
        self._logger = logger
        self._meta_controller = MetaParseController(logger)
        self._datastore = datastore
        self.set_base_wf_meta()
        self._auto_loader()

    def _auto_loader(self, dirpath: str = None, filename: str = None) -> None:
        def run_event_loop(dirpath: str, filename: str) -> None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._task = loop.create_task(self._startup_event(dirpath, filename))
            loop.run_forever()

        if not dirpath:
            dirpath = getRecipeDir()
        if not filename:
            filename = getRecipeFile()

        thread = threading.Thread(target=run_event_loop, daemon=True, args=(dirpath, filename))
        thread.start()

    async def _startup_event(self, dirpath, filename):
        asyncio.create_task(self._watch_recipe(dirpath, filename))

    async def _watch_recipe(self, dirpath: str, filename: str) -> Any:
        self._logger.debug(f"watch changeable recipe file: {dirpath}/{filename}")
        wf_filepath = os.path.join(dirpath, filename)
        try:
            async for changes in awatch(wf_filepath):
                await self._sync_dag_meta()
        except Exception as e:
            self._logger.error(traceback.format_exc())
            self._logger.warn(f"Not ready {wf_filepath} file")

    async def _sync_dag_meta(self):
        wf_meta = self._datastore.get_wf_meta_file_service()
        if wf_meta:
            updated_dag_meta = self._meta_controller.cvt_wf_to_dag(wf_meta)
            current_dag_meta = self._datastore.get_wf_meta_service()  # <--
            if current_dag_meta != updated_dag_meta:
                self._logger.debug("# SYNC UPDATE")
                self.set_base_wf_meta(wf_meta)
                self._logger.debug(updated_dag_meta)

    def change_wf_meta(self, updated_wf_meta: Dict) -> None:  # <--
        current_wf_meta = self._datastore.get_wf_meta_service()  # <--
        if current_wf_meta != updated_wf_meta:  # <--
            self._logger.debug("# SYNC UPDATE")  # <--
            self._datastore.set_wf_meta_file_service(updated_wf_meta)  # <--
            # self.set_base_wf_meta(updated_wf_meta)  # <--

    def extract_wf_common_info_service(self, wf_meta: Dict) -> Dict:
        wf_comm_meta = self._meta_controller.extract_wf_common_info_ctl(wf_meta)
        return wf_comm_meta

    def extract_wf_common_env_service(self, wf_meta: Dict) -> Dict:  # <--
        wf_env_pool = self._meta_controller.extract_wf_common_env_ctl(wf_meta)  # <--
        return wf_env_pool  # <--

    def extract_wf_node_env_service(self, wf_meta: Dict) -> Dict:  # <--
        wf_node_env_map_pool = self._meta_controller.extract_wf_node_env_map_ctl(wf_meta)  # <--
        return wf_node_env_map_pool  # <--

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

    def extract_params_map_service(self, start_nodes, wf_service_pool, wf_edges_meta) -> Dict:
        edge_params_map = self._meta_controller.extract_params_map_ctl(start_nodes, wf_service_pool, wf_edges_meta)
        return edge_params_map

    def set_base_wf_meta(self, wf_meta: Dict = None):
        if not wf_meta:
            wf_meta = self._datastore.get_wf_meta_file_service()

        self._logger.error("# [DAG Loader] Step 01. Extract Common Info")
        wf_comm_meta = self.extract_wf_common_info_service(wf_meta)
        self._datastore.set_comm_meta_service(wf_comm_meta)
        self._print_debug_data(wf_comm_meta)

        self._logger.error("# [DAG Loader] Step 02. Extract Resource Meta")
        wf_resources_meta = self.get_wf_to_resources_service(wf_meta)
        self._datastore.set_resources_meta_service(wf_resources_meta)
        self._print_debug_data(wf_resources_meta)

        self._logger.error("# [DAG Loader] Step 03. Extract Nodes")
        wf_nodes_meta = self.extract_wf_to_nodes_service(wf_meta)
        self._datastore.set_nodes_meta_service(wf_nodes_meta)
        self._print_debug_data(wf_nodes_meta)

        self._logger.error("# [DAG Loader] Step 04. Extract common environment params")
        wf_env_pool = self.extract_wf_common_env_service(wf_meta)
        self._print_debug_data(wf_env_pool)

        self._logger.error("# [DAG Loader] Step 05. Extract node - environment mapper")
        wf_node_env_map_pool = self.extract_wf_node_env_service(wf_meta)
        self._print_debug_data(wf_node_env_map_pool)

        self._logger.error("# [DAG Loader] Step 06. Extract node's environment params")
        nodes_env_value_map = self.extract_node_environments_value_map_service(wf_nodes_meta, wf_node_env_map_pool, wf_env_pool)
        self._datastore.set_init_nodes_env_params_service(nodes_env_value_map)
        self._print_debug_data(nodes_env_value_map)

        self._logger.error("# [DAG Loader] Step 07. Extract Service Pool")
        wf_service_pool = self.cvt_wf_to_service_pool_service(wf_nodes_meta)
        self._datastore.set_node_service_pool_service(wf_service_pool)
        self._print_debug_data(wf_service_pool)

        self._logger.error("# [DAG Loader] Step 08. Extract Edges")
        wf_edges_meta = self.extract_wf_to_edges_service(wf_meta, wf_service_pool)
        self._datastore.set_init_service_params_service(wf_edges_meta)
        self._datastore.set_edges_meta_service(wf_edges_meta)
        self._print_debug_data(wf_edges_meta)

        self._logger.error("# [DAG Loader] Step 09. Extract Forward-Edge graph")
        wf_forward_edge_graph = self.extract_forward_edge_graph_service(wf_edges_meta)
        self._datastore.set_forward_edge_graph_meta_service(wf_forward_edge_graph)
        self._print_debug_data(wf_forward_edge_graph)

        self._logger.error("# [DAG Loader] Step 10. Extract Forward-graph")
        wf_forward_graph = self.extract_forward_graph_service(wf_edges_meta)
        self._datastore.set_forward_graph_meta_service(wf_forward_graph)
        self._print_debug_data(wf_forward_graph)

        self._logger.error("# [DAG Loader] Step 11. Extract backward-graph")
        wf_backward_graph = self.extract_backward_graph_service(wf_edges_meta)
        self._datastore.set_backward_graph_meta_service(wf_backward_graph)
        self._print_debug_data(wf_backward_graph)

        self._logger.error("# [DAG Loader] Step 12. Extract Start Node from forward_graph")
        start_nodes = self.find_start_nodes_service(wf_forward_graph)
        self._datastore.set_start_nodes_meta_service(start_nodes)
        self._print_debug_data(start_nodes)

        self._logger.error("# [DAG Loader] Step 13. Extract End Node from backward_graph")
        end_nodes = self.find_end_nodes_service(wf_backward_graph)
        self._datastore.set_end_nodes_meta_service(end_nodes)
        self._print_debug_data(end_nodes)

        self._logger.error("# [DAG Loader] Step 14. Extract service params-map")
        edges_param_map = self.extract_params_map_service(start_nodes, wf_service_pool, wf_edges_meta)
        self._datastore.set_edges_param_map_service(edges_param_map)
        self._print_debug_data(edges_param_map)

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
