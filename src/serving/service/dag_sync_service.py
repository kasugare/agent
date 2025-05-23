#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.serving.access.file_lock import FileLock
from ..service.dag_meta_service import DAGLoader
from .graph.node_graph import GraphGenerator
from .workflow.workflow_manager import WorkflowManager
from watchfiles import awatch
import traceback
import asyncio
import json
import os


class DagSyncService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, logger=None):
        super().__init__(logger, tags=['serving'])
        self._graph = GraphGenerator(self._logger)
        self._workflow_engine = WorkflowManager(self._logger)

        self._nodes_meta = None
        self._dag_loader = None

        self._wf_meta_dir_path = "/Users/hanati/workspace/model_serving/recipe"
        self._wf_meta_file_name = "stt_serving.json"
        self._wf_meta_file_path = os.path.join(self._wf_meta_dir_path, self._wf_meta_file_name)
        self._init_service_meta()
        self._init_recipe(self._wf_meta_dir_path, self._wf_meta_file_name)
        self._start_background_loop()

    def _start_background_loop(self):
        def run_event_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._task = loop.create_task(self._startup_event())
            loop.run_forever()
        import threading
        thread = threading.Thread(target=run_event_loop, daemon=True)
        thread.start()

    async def _startup_event(self):
        asyncio.create_task(self._watch_recipe())

    def _init_recipe(self, dir_path, file_name):
        file_path = os.path.join(dir_path, file_name)
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
        if not os.path.exists(file_path):
            with FileLock("/Users/hanati/workspace/model_serving/lock/wf_stt_meta.lock"):
                with open(self._wf_meta_file_path, 'w') as fd:
                    json.dump({}, fd, indent=2)

    async def _watch_recipe(self):
        self._logger.critical(f"watch changeable recipe file: {self._wf_meta_file_name}")
        try:
            async for changes in awatch(self._wf_meta_file_path):
                await self._sync_recipe()
        except Exception as e:
            self._logger.error(traceback.format_exc())
            self._logger.warn(f"Not ready {self._wf_meta_file_path} file")

    async def _sync_recipe(self):
        if not os.path.exists(self._wf_meta_file_path):
            return

        with FileLock("/Users/hanati/workspace/model_serving/lock/wf_stt_meta.lock"):
            with open(self._wf_meta_file_path, 'r') as fd:
                try:
                    workflow_config = json.load(fd)
                except json.JSONDecodeError:
                    self._logger.error("Invalid routes file format")
                except Exception as e:
                    self._logger.error(traceback.format_exc())

        if workflow_config:
            nodes_meta = self._get_nodes_meta(workflow_config)
            if self._nodes_meta == nodes_meta:
                return
            else:
                self._logger.critical("# SYNC UPDATE")
                self._init_service_meta(workflow_config)
                self._logger.warn(self._nodes_meta)

    def _load_dag(self, config_dir: str = None, dag_filename: str = None):
        self._dag_loader = DAGLoader(self._logger, self._wf_meta_dir_path)
        workflow_config = self._dag_loader.load_dag(self._wf_meta_file_name)
        return workflow_config

    def _get_nodes_meta(self, workflow_config):
        if workflow_config:
            nodes_meta = workflow_config['nodes']
        else:
            nodes_meta = {}
        return nodes_meta
    #

    def _check_vaild_nodes(self, nodes_meta):
        node_ids = nodes_meta.keys()
        edge_node_ids = []
        for node_id in node_ids:
            edge_node_ids.extend(nodes_meta[node_id]['prev_nodes'])
            edge_node_ids.extend(nodes_meta[node_id]['next_nodes'])
        edge_node_ids = list(set(edge_node_ids))
        if set(node_ids) == set(edge_node_ids):
            return True
        else:
            return False

    def _init_service_meta(self, workflow_config=None):
        if not workflow_config:
            workflow_config = self._load_dag()

        nodes_meta = self._get_nodes_meta(workflow_config)
        if not self._check_vaild_nodes(nodes_meta):
            self._logger.error("invalid nodes to edge-nodes")
            return False

        edge_map = self._dag_loader.cvt_workflow_to_edge(nodes_meta)
        self._graph = GraphGenerator(self._logger)
        self._graph.set_nodes_meta_to_graph(edge_map)
        self._nodes_meta = nodes_meta

        return True

    def _set_workflow_meta(self, workflow_config):
        self._logger.critical("# Update")
        with FileLock("/Users/hanati/workspace/model_serving/lock/wf_stt_meta.lock"):
            if os.path.exists(self._wf_meta_file_path):
                with open(self._wf_meta_file_path, 'w') as fd:
                    json.dump(workflow_config, fd, indent=2)
                result = self._init_service_meta(workflow_config)
            else:
                with open(self._wf_meta_file_path, 'w') as fd:
                    json.dump(workflow_config, fd, indent=2)
                result = {}
        return result


    # def _get_edge_map(self, nodes_meta):
    #     edge_map = self._dag_loader.cvt_workflow_to_edge(nodes_meta)
    #     return edge_map
    #
    # def _get_edge_graph(self, edge_map):
    #     edge_graph = self._graph.set_nodes_meta_to_graph(edge_map)
    #     return edge_graph