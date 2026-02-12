#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.conf_serving import getRecipeDir
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
        self._start_nodes = []

    def valid_wf_config(self, dag_info: Dict) -> None:
        for field in REQUIRED_DAG_FIELDS:
            if field not in dag_info:
                self._logger.error(f"Not exist required filed: {field}")
                raise ValueError(f"Not exist required filed: {field}")

        for node_id, node in dag_info['nodes'].items():
            for field in REQUIRED_NODE_FIELDS:
                if field not in node:
                    self._logger.error(f"Not exist required node filed: {field}")
                    raise ValueError(f"Not exist required node filed: {field}")

        for edge in dag_info['edges']:
            for req_edge in REQUIRED_EDGE_FIELDS:
                if req_edge not in edge.keys():
                    self._logger.critical(edge)
                    self._logger.error(f"Not exist required edge filed: {edge}")
                    raise ValueError(f"Not exist required edge filed: {edge}")

    def valid_dag_meta(self, dag_meta: Dict) -> bool:
        node_ids = dag_meta.keys()
        edge_node_ids = []
        for node_id in node_ids:
            edge_node_ids.extend(dag_meta[node_id]['prev_nodes'])
            edge_node_ids.extend(dag_meta[node_id]['next_nodes'])
        edge_node_ids = list(set(edge_node_ids))
        if set(node_ids) == set(edge_node_ids):
            return True
        else:
            return False

    def set_dag(self, dag_meta:Dict) -> Dict:
        self._dag_meta = dag_meta

    def get_dag(self) -> Dict:
        return self._dag_meta

    def set_edge_map(self, edge_map:Dict) -> Dict:
        self._edge_map = edge_map

    def get_edge_map(self) -> Any:
        return self._edge_map

    def set_start_nodes(self, start_nodes:List[Any]) -> List[Any]:
        self._start_nodes = start_nodes

    def get_start_nodes(self) -> List[Any]:
        return self._start_nodes

    def set_metas(self, dag_meta, edge_map, start_nodes):
        self._thread_lock.acquire()
        self.set_dag(dag_meta)
        self.set_edge_map(edge_map)
        self.set_start_nodes(start_nodes)
        self._thread_lock.release()


class DagLoadService(DagLoader):
    def __init__(self, logger):
        super().__init__(logger)
        self._logger = logger
        self._dag_meta_controller = DagMetaController(logger)
        self.init_dag_meta()

    def start_background_loop(self, dirpath: str = None, filename: str = None) -> None:
        def run_event_loop(dirpath, filename):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._task = loop.create_task(self._startup_event(dirpath, filename))
            loop.run_forever()

        if not dirpath:
            dirpath = getRecipeDir()
        if not filename:
            filename = 'stt_serving.json'

        thread = threading.Thread(target=run_event_loop, daemon=True, args=(dirpath, filename))
        thread.start()

    async def _startup_event(self, dirpath, filename):
        asyncio.create_task(self._watch_recipe(dirpath, filename))

    async def _watch_recipe(self, dirpath:str, filename:str) -> Any:
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

    def init_dag_meta(self, wf_config=None) -> Dict:
        if not wf_config:
            wf_config = self._dag_meta_controller.load_wf_config()
        dag_meta = self._dag_meta_controller.cvt_wf_to_dag(wf_config)
        if not self.valid_dag_meta(dag_meta):
            self._logger.error("invalid nodes to edge-nodes")
            return

        edge_map = self._dag_meta_controller.cvt_wf_to_edge(dag_meta)
        start_nodes = self._dag_meta_controller.find_start_nodes(edge_map)
        self.set_metas(dag_meta, edge_map, start_nodes)

    def get_wf_config(self) -> Dict:
        wf_config = self._dag_meta_controller.load_wf_config()
        dag_meta = self._dag_meta_controller.cvt_wf_to_dag(wf_config)
        self.valid_dag_meta(dag_meta)
        return wf_config

    def set_wf_config(self, wf_config:Dict) -> None:
        self._logger.critical("# Update")
        self._dag_meta_controller.save_wf_config(wf_config)

    def change_dag_meta(self, wf_config:Dict) -> Dict:
        self.init_dag_meta(wf_config)
        dag_meta = self.get_dag()
        if dag_meta:
            self.set_wf_config(wf_config)