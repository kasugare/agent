#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from typing import Dict, List
from fastapi import Depends
from redis import Redis
from api.workflow.common.redis.redis_access import RedisAccess
from common.dependancy import get_redis_client


class RemoteCachedMetastoreAccess(RedisAccess):
    def __init__(self, logger, wf_id=None):
        super().__init__(logger)
        if wf_id:
            self._cache_key = f'{wf_id}.meta'
        else:
            self._cache_key = None

    def set_cache_key_access(self, wf_id):
        self._cache_key = f'{wf_id}.meta'

    def clear_access(self):
        self.flush()

    def set_wf_meta_access(self, wf_meta: Dict) -> None:
        self.hset(key=self._cache_key, mapping={'wf_meta': json.dumps(wf_meta)})

    def get_wf_meta_access(self) -> Dict:
        return self.hget(key=self._cache_key, field='wf_meta')

    def set_project_id_access(self, project_id: str) -> None:
        self.hset(key=self._cache_key, mapping={'proj_id': json.dumps(project_id)})

    def get_project_id_access(self):
        return self.hget(key=self._cache_key, field="proj_id")

    def set_workflow_id_access(self, workflow_id: str) -> None:
        self.hset(key=self._cache_key, mapping={'wf_id': json.dumps(workflow_id)})

    def get_workflow_id_access(self):
        return self.hget(key=self._cache_key, field="wf_id")

    def set_comm_meta_access(self, wf_comm_meta: Dict) -> None:
        self.hset(key=self._cache_key, mapping={'comm_meta': json.dumps(wf_comm_meta)})

    def get_comm_meta_access(self) -> Dict:
        return self.hget(key=self._cache_key, field='comm_meta')

    def set_env_pool_access(self, wf_env_pool: Dict) -> None:
        self.hset(key=self._cache_key, mapping={'wf_env': json.dumps(wf_env_pool)})

    def get_env_pool_access(self) -> Dict:
        return self.hget(key=self._cache_key, field='wf_env')

    def set_nodes_env_value_map_access(self, wf_nodes_env_map_pool: Dict) -> None:
        self.hset(key=self._cache_key, mapping={'nodes_env_map': json.dumps(wf_nodes_env_map_pool)})

    def get_nodes_env_value_map_access(self) -> Dict:
        return self.hget(key=self._cache_key, field='nodes_env_map')

    def set_nodes_asset_value_map_access(self, wf_nodes_asset_map_pool: Dict) -> None:
        self.hset(key=self._cache_key, mapping={'nodes_asset_map': json.dumps(wf_nodes_asset_map_pool)})

    def get_nodes_asset_value_map_access(self) -> Dict:
        return self.hget(key=self._cache_key, field='nodes_asset_map')

    def set_nodes_meta_access(self, wf_nodes_meta: Dict) -> None:
        self.hset(key=self._cache_key, mapping={'nodes_meta': json.dumps(wf_nodes_meta)})

    def get_nodes_meta_access(self) -> Dict:
        return self.hget(key=self._cache_key, field='nodes_meta')

    def set_node_service_pool_access(self, wf_service_pool: Dict) -> None:
        self.hset(key=self._cache_key, mapping={'service_pool': json.dumps(wf_service_pool)})

    def get_node_service_pool_access(self) -> Dict:
        return self.hget(key=self._cache_key, field='service_pool')

    def set_edges_meta_access(self, wf_edges_meta: Dict) -> None:
        self.hset(key=self._cache_key, mapping={'edges_meta': json.dumps(wf_edges_meta)})

    def get_edges_meta_access(self) -> List:
        return self.hget(key=self._cache_key, field='edges_meta')

    def set_custom_result_meta_access(self, custom_result_meta: Dict) -> None:
        self.hset(key=self._cache_key, mapping={'custom_result_meta': json.dumps(custom_result_meta)})

    def get_custom_result_meta_access(self):
        return self.hget(key=self._cache_key, field='custom_result_meta')

    def get_custom_result_meta_by_service_id_access(self, service_id):
        custom_result_meta = self.get_custom_result_meta_access()
        custom_result = custom_result_meta.get(service_id)
        return custom_result

    def set_forward_edge_graph_meta_access(self, wf_forward_edge_graph: Dict) -> None:
        self.hset(key=self._cache_key, mapping={'forward_edge_graph': json.dumps(wf_forward_edge_graph)})

    def get_forward_edges_graph_meta_access(self) -> List:
        return self.hget(key=self._cache_key, field='forward_edge_graph')

    def set_forward_graph_meta_access(self, wf_forward_graph: Dict) -> None:
        self.hset(key=self._cache_key, mapping={'forward_graph': json.dumps(wf_forward_graph)})

    def get_forward_graph_meta_access(self) -> List:
        return self.hget(key=self._cache_key, field='forward_graph')

    def set_backward_graph_meta_access(self, wf_backward_graph: Dict) -> None:
        self.hset(key=self._cache_key, mapping={'backward_graph': json.dumps(wf_backward_graph)})

    def get_backward_graph_meta_access(self) -> List:
        return self.hget(key=self._cache_key, field='backward_graph')

    def set_resources_meta_access(self, wf_resources_meta: Dict) -> None:
        self.hset(key=self._cache_key, mapping={'resources_meta': json.dumps(wf_resources_meta)})

    def get_resources_meta_access(self) -> Dict:
        return self.hget(key=self._cache_key, field='resources_meta')

    def set_start_nodes_meta_access(self, start_nodes: list) -> None:
        self.hset(key=self._cache_key, mapping={'start_nodes': json.dumps(start_nodes)})

    def get_start_nodes_meta_access(self) -> List:
        return self.hget(key=self._cache_key, field='start_nodes')

    def set_end_nodes_meta_access(self, end_nodes: list) -> None:
        self.hset(key=self._cache_key, mapping={'end_nodes': json.dumps(end_nodes)})

    def get_end_nodes_meta_access(self) -> List:
        return self.hget(key=self._cache_key, field='end_nodes')

    def set_edges_param_map_access(self, edges_param_map: dict) -> None:
        self.hset(key=self._cache_key, mapping={'edges_param_map': json.dumps(edges_param_map)})

    def get_edges_param_map_access(self) -> List:
        return self.hget(key=self._cache_key, field='edges_param_map')

    def get_dag_access(self) -> List:
        return self.hget(key=self._cache_key, field='dag')


