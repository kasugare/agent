#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.conf_system import getRecipeDir, getRecipeFile
from api.serving.control.dag_meta_controller import DagMetaController
from typing import Dict, List, Any
from watchfiles import awatch
import traceback
import threading
import asyncio
import os

REQUIRED_DAG_FIELDS = ['nodes', 'edges']
REQUIRED_NODE_FIELDS = ['id', 'type', 'prev_nodes', 'next_nodes']
REQUIRED_EDGE_FIELDS = ['source', 'target']


class DagLoader:
    def __init__(self, logger):
        self._logger = logger
        self._thread_lock = threading.Lock()
        self._dag_meta = {}
        self._edge_map = {}

        self._wf_comm_meta = {}
        self._wf_nodes_meta = {}
        self._wf_node_service_pool = {}
        self._wf_edges_meta = []
        self._wf_edges_grape = {}
        self._wf_prev_edge_grape = {}
        self._wf_resources_meta = {}
        self._start_node = None

    def set_comm_meta(self, wf_comm_meta: Dict) -> None:
        self._wf_comm_meta = wf_comm_meta

    def set_nodes_meta(self, wf_nodes_meta: Dict) -> None:
        self._wf_nodes_meta = wf_nodes_meta

    def set_node_service_pool(self, wf_service_pool: Dict) -> None:
        self._wf_node_service_pool = wf_service_pool

    def set_edges_meta(self, wf_edges_meta: Dict) -> None:
        self._wf_edges_meta = wf_edges_meta

    def set_edges_grape_meta(self, wf_edges_grape: Dict) -> None:
        self._wf_edges_grape = wf_edges_grape

    def set_prev_edge_grape_meta(self, wf_prev_edge_grape: Dict) -> None:
        self._wf_prev_edge_grape = wf_prev_edge_grape

    def set_resources_meta(self, wf_resources_meta: Dict) -> None:
        self._wf_resources_meta = wf_resources_meta

    def set_start_node_meta(self, start_node: str) -> None:
        self._start_node = start_node

    def get_dag(self) -> Dict:
        return self._dag_meta

    def get_comm_meta(self) -> Dict:
        return self._wf_comm_meta

    def get_node_service_pool(self) -> Dict:
        return self._wf_node_service_pool

    def get_nodes_meta(self) -> Dict:
        return self._wf_nodes_meta

    def get_edges_meta(self) -> Dict:
        return self._wf_edges_meta

    def get_edges_grape_meta(self) -> Dict:
        return self._wf_edges_grape

    def get_prev_edges_grpae_meta(self) -> Dict:
        return self._wf_prev_edge_grape

    def get_resources_meta(self) -> Dict:
        return self._wf_resources_meta

    def get_start_node_meta(self) -> str:
        return self._start_node

    def set_metas(self, wf_comm_meta, wf_nodes_meta, wf_service_pool, wf_edges_meta,
                  wf_edges_grape, wf_prev_edge_grape, wf_resources_meta, start_node):
        self._thread_lock.acquire()
        self.set_comm_meta(wf_comm_meta)
        self.set_nodes_meta(wf_nodes_meta)
        self.set_node_service_pool(wf_service_pool)
        self.set_edges_meta(wf_edges_meta)
        self.set_edges_grape_meta(wf_edges_grape)
        self.set_prev_edge_grape_meta(wf_prev_edge_grape)
        self.set_resources_meta(wf_resources_meta)
        self.set_start_node_meta(start_node)
        self._thread_lock.release()

    def get_meta_pack(self):
        meta_pack = {
            "start_node": self.get_start_node_meta(),
            "nodes_info": self.get_nodes_meta(),
            "service_pool": self.get_node_service_pool(),
            "edges_info": self.get_edges_meta(),
            "edges_grape": self.get_edges_grape_meta(),
            "prev_edges_grape": self.get_prev_edges_grpae_meta()
        }
        return meta_pack


class DagLoadService(DagLoader):
    def __init__(self, logger):
        super().__init__(logger)
        self._logger = logger
        self._dag_meta_controller = DagMetaController(logger)
        self.init_dag_meta()

    def start_background_loop(self, dirpath: str = None, filename: str = None) -> None:
        def run_event_loop(dirpath: str, filename: str):
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
        self._logger.critical(f"watch changeable recipe file: {dirpath}/{filename}")
        wf_filepath = os.path.join(dirpath, filename)
        try:
            async for changes in awatch(wf_filepath):
                await self._sync_dag_meta()
        except Exception as e:
            self._logger.error(traceback.format_exc())
            self._logger.warn(f"Not ready {wf_filepath} file")

    async def _sync_dag_meta(self):
        wf_config = self.get_wf_config()
        if wf_config:
            updated_dag_meta = self._dag_meta_controller.cvt_wf_to_dag(wf_config)
            current_dag_meta = self.get_dag()
            if current_dag_meta != updated_dag_meta:
                self._logger.critical("# SYNC UPDATE")
                self.init_dag_meta(wf_config)
                self._logger.warn(updated_dag_meta)

    def init_dag_meta(self, wf_config: Dict = None) -> Dict:
        if not wf_config:
            wf_config = self._dag_meta_controller.load_wf_config()

        self._logger.error("# [DAG Loader] Step 1. Extract Common Info")
        wf_comm_meta = self._dag_meta_controller.get_wf_common_info(wf_config)

        self._logger.error("# [DAG Loader] Step 2. Extract Nodes")
        wf_nodes_meta = self._dag_meta_controller.get_wf_to_nodes(wf_config)
        # for k, v in wf_nodes_meta.items():
        #     self._logger.debug(f" - {k} : {v}")

        self._logger.error("# [DAG Loader] Step 3. Extract Service Pool")
        wf_service_pool = self._dag_meta_controller.cvt_wf_to_service_pool(wf_nodes_meta)
        # for k, v in wf_service_pool.items():
        #     self._logger.debug(f" - {k} : {v}")

        self._logger.error("# [DAG Loader] Step 4. Extract Edges")
        wf_edges_meta = self._dag_meta_controller.get_wf_to_edges(wf_config, wf_service_pool)

        self._logger.error("# [DAG Loader] Step 5. Extract Grape")
        wf_edges_grape = self._dag_meta_controller.cvt_edge_to_grape(wf_edges_meta)
        for k, v in wf_edges_grape.items():
            self._logger.debug(f" - {k} : {v}")

        self._logger.error("# [DAG Loader] Step 6. Extract Prev-Grape")
        wf_prev_edge_grape = self._dag_meta_controller.get_edges_to_prev_nodes(wf_edges_meta)
        for k, v in wf_prev_edge_grape.items():
            self._logger.debug(f" - {k} : {v}")

        self._logger.error("# [DAG Loader] Step 7. Extract Resource Meta")
        wf_resources_meta = self._dag_meta_controller.get_wf_to_resources(wf_config)

        self._logger.error("# [DAG Loader] Step 8. Extract Start Node from edges_grape")
        start_node = self._dag_meta_controller.find_start_node(wf_edges_grape)
        # start_nodes = self._dag_meta_controller.find_start_nodes(wf_edges_grape)

        self._logger.error("# [DAG Loader] Step 9. Set all metas")
        self.set_metas(wf_comm_meta, wf_nodes_meta, wf_service_pool, wf_edges_meta,
                       wf_edges_grape, wf_prev_edge_grape, wf_resources_meta, start_node)

    def get_wf_config(self) -> Dict:
        wf_config = self._dag_meta_controller.load_wf_config()
        return wf_config

    def set_wf_config(self, wf_config: Dict) -> None:
        self._logger.critical("# Update")
        self._dag_meta_controller.save_wf_config(wf_config)

    def change_dag_meta(self, wf_config: Dict) -> None:
        self.init_dag_meta(wf_config)
        dag_meta = self.get_dag()
        if dag_meta:
            self.set_wf_config(wf_config)