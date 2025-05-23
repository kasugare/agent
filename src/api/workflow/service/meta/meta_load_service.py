#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.conf_system import getRecipeDir, getRecipeFile
from api.workflow.control.meta.meta_parse_controller import MetaParseController
from typing import Dict, List, Any
from watchfiles import awatch
import traceback
import threading
import asyncio
import os


class MetaLoadService:
    def __init__(self, logger, datastore):
        self._logger = logger
        self._meta_controller = MetaParseController(logger)
        self._datastore = datastore
        self.init_wf_meta()
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
        wf_meta = self._datastore.get_wf_meta_file()
        if wf_meta:
            updated_dag_meta = self._meta_controller.cvt_wf_to_dag(wf_meta)
            current_dag_meta = self._datastore.get_dag()
            if current_dag_meta != updated_dag_meta:
                self._logger.debug("# SYNC UPDATE")
                self.init_wf_meta(wf_meta)
                self._logger.debug(updated_dag_meta)

    # 수정 필요
    def change_wf_meta(self, wf_req_meta: Dict) -> None:
        wf_file_mata = self._datastore.get_wf_meta_file()
        if wf_file_mata != wf_file_mata:
            self._datastore.set_wf_meta(wf_req_meta)
            # self.init_dag_meta(wf_req_meta)

    def init_wf_meta(self, wf_meta: Dict = None) -> Dict:
        if not wf_meta:
            wf_meta = self._datastore.get_wf_meta_file()

        self._logger.error("# [DAG Loader] Step 1. Extract Common Info")
        wf_comm_meta = self._meta_controller.extract_wf_common_info(wf_meta)
        self._print_debug_data(wf_comm_meta)

        self._logger.error("# [DAG Loader] Step 2. Extract Nodes")
        wf_nodes_meta = self._meta_controller.extract_wf_to_nodes(wf_meta)
        self._print_debug_data(wf_nodes_meta)

        self._logger.error("# [DAG Loader] Step 3. Extract Service Pool")
        wf_service_pool = self._meta_controller.cvt_wf_to_service_pool(wf_nodes_meta)
        self._print_debug_data(wf_service_pool)

        self._logger.error("# [DAG Loader] Step 4. Extract Edges")
        wf_edges_meta = self._meta_controller.extract_wf_to_edges(wf_meta, wf_service_pool)
        self._print_debug_data(wf_edges_meta)

        self._logger.error("# [DAG Loader] Step 5. Extract Grape")
        wf_edges_grape = self._meta_controller.extract_sequenceal_edge_to_grape(wf_edges_meta)
        self._print_debug_data(wf_edges_grape)

        self._logger.error("# [DAG Loader] Step 6. Extract Prev-Grape")
        wf_prev_edge_grape = self._meta_controller.extract_reverse_edge_grape(wf_edges_meta)
        self._print_debug_data(wf_prev_edge_grape)

        self._logger.error("# [DAG Loader] Step 7. Extract Resource Meta")
        wf_resources_meta = self._meta_controller.get_wf_to_resources(wf_meta)
        self._print_debug_data(wf_resources_meta)

        self._logger.error("# [DAG Loader] Step 8. Extract Start Node from edges_grape")
        start_nodes = self._meta_controller.find_start_nodes(wf_edges_grape)
        self._print_debug_data(start_nodes)

        self._logger.error("# [DAG Loader] Step 9. Extract End Node from prev_edges_grape")
        end_nodes = self._meta_controller.find_end_nodes(wf_prev_edge_grape)
        self._print_debug_data(end_nodes)

        self._logger.error("# [DAG Loader] Step 10. Set all metas")
        self._datastore.set_meta_pack(wf_comm_meta, wf_nodes_meta, wf_service_pool, wf_edges_meta,
                       wf_edges_grape, wf_prev_edge_grape, wf_resources_meta, start_nodes, end_nodes)

    def _print_debug_data(self, debug_data) -> None:
        if isinstance(debug_data, dict):
            for k, v in debug_data.items():
                self._logger.debug(f"  - {k} : {v}")
        elif isinstance(debug_data, list):
            for l in debug_data:
                self._logger.debug(f"  - {l}")
        else:
            self._logger.debug(f"  - {debug_data}")
