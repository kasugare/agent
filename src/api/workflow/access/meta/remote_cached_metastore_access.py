#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from typing import Dict, List
from fastapi import Depends
from redis import Redis
from api.workflow.common.redis.redis_access import RedisAccess
from common.dependancy import get_redis_client


class RemoteCachedMetastoreAccess(RedisAccess):
    def __init__(self, logger):
        super().__init__(logger)
        # self.project_id = redis_client_info.project_id
        # self.workflow_id = redis_client_info.workflow_id
        # self._redis_key = f"{self.project_id}-{self.workflow_id}.metapool"
        self._redis_key = 'project1-workflow1.metapool'

    def set_wf_meta_access(self, wf_meta: Dict) -> None:
        self.hset(key=self._redis_key, mapping={'wf_meta': json.dumps(wf_meta)})

    def get_wf_meta_access(self) -> Dict:
        return self.hget(key=self._redis_key, field='wf_meta')

    def set_comm_meta_access(self, wf_comm_meta: Dict) -> None:
        self.hset(key=self._redis_key, mapping={'comm_meta': json.dumps(wf_comm_meta)})

    def get_comm_meta_access(self) -> Dict:
        return self.hget(key=self._redis_key, field='comm_meta')

    def set_nodes_meta_access(self, wf_nodes_meta: Dict) -> None:
        self.hset(key=self._redis_key, mapping={'nodes_meta': json.dumps(wf_nodes_meta)})

    def get_nodes_meta_access(self) -> Dict:
        return self.hget(key=self._redis_key, field='nodes_meta')

    def set_node_service_pool_access(self, wf_service_pool: Dict) -> None:
        self.hset(key=self._redis_key, mapping={'service_pool': json.dumps(wf_service_pool)})

    def get_node_service_pool_access(self) -> Dict:
        return self.hget(key=self._redis_key, field='service_pool')

    def set_edges_meta_access(self, wf_edges_meta: Dict) -> None:
        self.hset(key=self._redis_key, mapping={'edges_meta': json.dumps(wf_edges_meta)})

    def get_edges_meta_access(self) -> List:
        return self.hget(key=self._redis_key, field='edges_meta')

    def set_forward_edge_graph_meta_access(self, wf_forward_edge_graph: Dict) -> None:
        self.hset(key=self._redis_key, mapping={'forward_edge_graph': json.dumps(wf_forward_edge_graph)})

    def get_forward_edges_graph_meta_access(self) -> List:
        return self.hget(key=self._redis_key, field='forward_edge_graph')

    def set_forward_graph_meta_access(self, wf_forward_graph: Dict) -> None:
        self.hset(key=self._redis_key, mapping={'forward_graph': json.dumps(wf_forward_graph)})

    def get_forward_graph_meta_access(self) -> List:
        return self.hget(key=self._redis_key, field='forward_graph')

    def set_backward_graph_meta_access(self, wf_backward_graph: Dict) -> None:
        self.hset(key=self._redis_key, mapping={'backward_graph': json.dumps(wf_backward_graph)})

    def get_backward_graph_meta_access(self) -> List:
        return self.hget(key=self._redis_key, field='backward_graph')

    def set_resources_meta_access(self, wf_resources_meta: Dict) -> None:
        self.hset(key=self._redis_key, mapping={'resources_meta': json.dumps(wf_resources_meta)})

    def get_resources_meta_access(self) -> Dict:
        return self.hget(key=self._redis_key, field='resources_meta')

    def set_start_nodes_meta_access(self, start_nodes: list) -> None:
        self.hset(key=self._redis_key, mapping={'start_nodes': json.dumps(start_nodes)})

    def get_start_nodes_meta_access(self) -> List:
        return self.hget(key=self._redis_key, field='start_nodes')

    def set_end_nodes_meta_access(self, end_nodes: list) -> None:
        self.hset(key=self._redis_key, mapping={'end_nodes': json.dumps(end_nodes)})

    def get_end_nodes_meta_access(self) -> List:
        return self.hget(key=self._redis_key, field='end_nodes')

    def set_edges_param_map_access(self, edges_param_map: dict) -> None:
        self.hset(key=self._redis_key, mapping={'edges_param_map': json.dumps(edges_param_map)})

    def get_edges_param_map_access(self) -> List:
        return self.hget(key=self._redis_key, field='edges_param_map')

    def get_dag_access(self) -> List:
        return self.hget(key=self._redis_key, field='dag')


