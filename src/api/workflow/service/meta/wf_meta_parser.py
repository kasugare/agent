#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.service.meta.wf_meta_handler import WorkflowMetaHandler
from api.workflow.control.meta.meta_parse_controller import MetaParseController
from typing import Dict, List, Any


class WorkflowMetaParser(WorkflowMetaHandler):
    def __init__(self, logger):
        super().__init__(logger)

        self._logger = logger
        self._meta_controller = MetaParseController(logger)

    def parse_wf_meta(self, wf_meta: Dict):
        try:
            if not wf_meta:
                return

            self._logger.info("# [DAG Loader] Step 01. Extract Common Info")
            wf_comm_meta = self.extract_wf_common_info_service(wf_meta)
            self._print_debug_data(wf_comm_meta)

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

            meta_pack = {
                "wf_meta": wf_meta,
                "common": wf_comm_meta,
                "project_id": wf_comm_meta.get('proj_id'),
                "workflow_id": wf_comm_meta.get('wf_id'),
                "start_nodes": start_nodes,
                "end_nodes": end_nodes,
                "resources": wf_resources_meta,
                "nodes_info": wf_nodes_meta,
                "service_pool": wf_service_pool,
                "edges_info": wf_edges_meta,
                "custom_result_info": custom_result_meta,
                "forward_edge_graph": wf_forward_edge_graph,
                "forward_graph": wf_forward_graph,
                "backward_graph": wf_backward_graph,
                "edges_param_map": edges_param_map,
                "env_pool": wf_env_pool,
                "nodes_env_value_map": nodes_env_value_map,
                "nodes_asset_value_map": nodes_asset_value_map
            }

            # self._metastore.set_comm_meta_service(wf_comm_meta) # metastore
            # self._metastore.set_env_pool_service(wf_env_pool) # metastore
            # self._metastore.set_resources_meta_service(wf_resources_meta) # metastore
            # self._metastore.set_nodes_meta_service(wf_nodes_meta) # metastore
            # self._metastore.set_node_service_pool_service(wf_service_pool) # metastore
            # self._metastore.set_edges_meta_service(wf_edges_meta) # metastore
            #
            # self._metastore.set_nodes_env_value_map_service(nodes_env_value_map) # metastore
            # self._metastore.set_nodes_asset_value_map_service(nodes_asset_value_map)  # metastore
            #
            # self._metastore.set_custom_result_meta_service(custom_result_meta) # metastore
            # self._metastore.set_forward_edge_graph_meta_service(wf_forward_edge_graph) # metastore
            # self._metastore.set_forward_graph_meta_service(wf_forward_graph) # metastore
            # self._metastore.set_backward_graph_meta_service(wf_backward_graph) # metastore
            # self._metastore.set_start_nodes_meta_service(start_nodes) # metastore
            # self._metastore.set_end_nodes_meta_service(end_nodes) # metastore
            # self._metastore.set_edges_param_map_service(edges_param_map) # metastore

            # self._metastore.set_init_service_params_service(wf_edges_meta) # dataio - meta_pack: edges_info
            # self._metastore.set_init_nodes_env_params_service(nodes_env_value_map) # dataio
            # self._metastore.set_init_nodes_asset_params_service(nodes_asset_value_map) # dataio
            self._meta_pack = meta_pack
        except Exception as e:
            self._logger.error("Wrong workflow meta")
            raise
        return self._meta_pack

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
