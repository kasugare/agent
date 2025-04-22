#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ailand.common.logger import Logger
from recipe.recipe_manager import DAGLoader
from graph.node_graph import GraphGenerator
from workflow.workflow_manager import WorkflowManager


class ServingProvider:
    def __init__(self):
        self._logger = Logger().getLogger()
        self._graph = GraphGenerator(self._logger)
        self._workflow_manager = WorkflowManager(self._logger, self._graph)

        self._workflow_config = None
        self._dag_loader = None

    def _load_dag(self, config_dir: str = None, dag_filename: str = None):
        if not dag_filename:
            dag_filename = 'workflow.json'

        if not config_dir:
            config_dir = '/Users/hanati/workspace/model_serving/recipe'

        self._dag_loader = DAGLoader(self._logger, config_dir)
        workflow_config = self._dag_loader.load_dag(dag_filename)
        return workflow_config

    def _get_nodes_meta(self, workflow_config):
        nodes_meta = workflow_config['nodes']
        return nodes_meta

    def _get_edge_map(self, nodes_meta):
        edge_map = self._dag_loader.cvt_workflow_to_edge(nodes_meta)
        return edge_map

    def _get_edge_graph(self, edge_map):
        edge_graph = self._graph.set_nodes_meta_to_graph(edge_map)
        return edge_graph

    def do_process(self):
        workflow_config = self._load_dag()
        nodes_meta = self._get_nodes_meta(workflow_config)
        edge_map = self._get_edge_map(nodes_meta)
        edge_meta = self._get_edge_graph(edge_map)
        self._workflow_manager.set_meta(nodes_meta, edge_meta)
        self._workflow_manager.run_workflow()


if __name__ == "__main__":
    service = ServingProvider()
    service.do_process()