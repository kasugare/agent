#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.service.meta.meta_load_service import MetaLoadService
from api.workflow.service.data.data_store_service import DataStoreService
from api.workflow.service.execute.workflow_execution_orchestrator import WorkflowExecutionOrchestrator
from multiprocessing import Process, Queue
from typing import Dict, Any
from abc import abstractmethod
from fastapi import APIRouter
from threading import Thread
import json
import time

class BaseRouter:
    def __init__(self, logger=None, tags=[]):
        self._logger = logger
        self.router = APIRouter(tags=tags)
        self.setup_routes()

    @abstractmethod
    def setup_routes(self):
        pass

    def get_router(self) -> APIRouter:
        return self.router


class WorkflowEngine(BaseRouter):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, logger=None, db_conn=None):
        super().__init__(logger, tags=['serving'])
        self._datastore = DataStoreService(logger)
        self._meta_service = MetaLoadService(logger, self._datastore)
        self._job_Q = Queue()

    def print_map(self, data_map):
        print("-" * 200)
        for k, v in data_map.items():
            self._logger.debug(f"{k} : {v}")

    def get_related_graph2(self, base_graph, from_node_id, count=0):
        count += 1
        space = " " * count * 4

        print(space, f"@[{count}] < {from_node_id} >")
        node_graph_list = base_graph.get(from_node_id)
        print(space, f" [{count}] # Step 0: has child nodes - {node_graph_list}")

        if not node_graph_list:
            print(space, f" [{count}] # Step -1")
            return None

        print(space, f" [{count}] # Step 1: Checking...")
        task_graph = {}
        for node_id in node_graph_list:
            print(space, f" [{count}] # Step 2: select child node - {node_id}")
            if base_graph.get(node_id):
                print(space, f" [{count}] # Step 3: recursive -  {node_id}")
                if task_graph.get(from_node_id):
                    task_graph[from_node_id].append(node_id)
                else:
                    task_graph[from_node_id] = [node_id]
                related_graph = self.get_related_graph2(base_graph, node_id, count)
                if related_graph:
                    print(space, f" [{count}] # Step 4: return recursive -  {related_graph}")
                    if task_graph.get(node_id):
                        print(space, f" [{count}] # Step 5: Add On - {node_id}")
                        task_graph[from_node_id].append(node_id)
                    else:
                        print(space, f" [{count}] # Step 6: New One - {node_id}")
                        task_graph[from_node_id] = [node_id]
                    print(space, f" [{count}] # Step 7: Grape Update - {node_id}")
                    task_graph.update(related_graph)
            else:
                print(space, f" [{count}] # Step 8: not found, recursive - {node_id}")
                task_graph[from_node_id] = []
        return task_graph

    def get_related_graph(self, service_graph, base_graph, from_node_id, count=0):
        count += 1
        space = " " * count * 4

        print(space, f"@[{count}] < {from_node_id} >")
        node_graph_list = base_graph.get(from_node_id)
        print(space, f" [{count}] # Step 0: has child nodes - {node_graph_list}")
        if not node_graph_list:
            print(space, f" [{count}] # Step -1")
            service_graph[from_node_id] = []
            return service_graph

        print(space, f" [{count}] # Step 1: Checking...")
        service_graph[from_node_id] = []
        for node_id in node_graph_list:
            print(space, f" [{count}] # Step 2: select child node - {node_id}")
            print(space, f" [{count}] # Step 3: recursive -  {node_id}")
            self.get_related_graph(service_graph, base_graph, node_id, count)
            print(space, f" [{count}] # Step 4: Add On - {node_id}")
            service_graph[from_node_id].append(node_id)
        print(space, f" [{count}] # Step 5: return node - {from_node_id}")
        return service_graph

    def find_graph(self, base_graph, from_node_id, to_node_id, count=0):
        count += 1
        space = " " * count * 4
        task_graph = {}
        print(space, f"@[{count}] < {from_node_id} -> {to_node_id} >")
        node_graph_list = base_graph.get(from_node_id)
        print(space, f" [{count}] # Step 0: has child nodes - {node_graph_list}")
        if not node_graph_list:
            print(space, f" [{count}] # Step -1")
            return None

        if from_node_id == to_node_id:
            task_graph[from_node_id] = [to_node_id]
            return task_graph

        print(space, f" [{count}] # Step 1: Checking...")

        for node_id in node_graph_list:
            print(space, f" [{count}] # Step 2: select child node - {node_id}")
            if node_id == to_node_id:
                print(space, f" [{count}] # Step 3: found!!  {node_id}")
                if task_graph.get(from_node_id):
                    task_graph[from_node_id].append(node_id)
                else:
                    task_graph[from_node_id] = [node_id]
                self.print_map(task_graph)
            else:
                print(space, f" [{count}] # Step 4: not found, recursive - {node_id}")
                task_graph2 = self.find_graph(base_graph, node_id, to_node_id, count)
                print(space, f" [{count}] # Step 5: {task_graph2}")
                if task_graph2:
                    print(space, f" [{count}] # Step 6: registration nodes")
                    if task_graph.get(from_node_id):
                        print(space, f" [{count}] # Step 7: already existed from_node - {from_node_id}")
                        task_graph[from_node_id].append(node_id)
                    else:
                        print(space, f" [{count}] # Step 8: not existed from_node, NEW- {from_node_id}")
                        task_graph[from_node_id] = [node_id]
                    print(space, f" [{count}] # Step 9: update found graph to task graph")
                    task_graph.update(task_graph2)

                    print(space, f" [{count}] # Step 8: completed registration")
                    self.print_map(task_graph)
                else:
                    print(space, f" [{count}] # Step 9: not exist nodes")
        print(space, f" [{count}] # Step 10: {task_graph}")
        return task_graph


    def setup_routes(self):
        @self.router.post(path='/workflow/meta')
        async def create_workflow(workflow) -> None:
            wf_meta = json.loads(workflow)
            self._meta_service.change_wf_meta(wf_meta)
            # return self._meta_service.get_dag()

        @self.router.post(path='/workflow/run/all')
        async def call_chained_model_service(request: Dict[str, Any]):
            if request and 'request_id' in list(request.keys()):
                request_id = request.pop('request_id')
            else:
                request_id = "AUTO_%X" %(int(time.time() * 10000))
            request['request_id'] = request_id
            workflow_engine = WorkflowExecutionOrchestrator(self._logger, self._datastore, self._job_Q)
            result = workflow_engine.run_workflow(request)
            return {"result": result}

        @self.router.post(path='/workflow/run/part')
        async def call_chained_model_service(request: Dict[str, Any]):
            start_node = request.get('from')
            end_node = request.get('to')
            forward_graph = self._datastore.get_forward_graph_meta()
            reverse_graph = self._datastore.get_reverse_graph_meta()

            service_graph = {}
            if start_node and not end_node:
                self._logger.info(f"# {start_node} --> END")
                self.print_map(forward_graph)
                # service_graph = self.get_related_graph2(forward_graph, start_node)
                service_graph = self.get_related_graph(service_graph, forward_graph, start_node)
                if not service_graph:
                    service_graph = {}
                    service_graph[start_node] = []
            elif not start_node and end_node:
                self._logger.info(f"# START --> {end_node}")
                self.print_map(reverse_graph)
                # service_graph = self.get_related_graph2(reverse_graph, end_node)
                service_graph = self.get_related_graph(service_graph, reverse_graph, end_node)
                if not service_graph:
                    service_graph[end_node] = []
            elif start_node and end_node:
                self._logger.info(f"# {start_node} --> {end_node}")
                self.print_map(forward_graph)
                service_graph = self.find_graph(forward_graph, start_node, end_node)
            else:
                pass
            self.print_map(service_graph)
            return {"result": 'result'}

        @self.router.get(path='/workflow/datapool')
        async def call_data_pool():
            self._logger.debug("-------------------------< Data Pool >-------------------------")
            data_pool = self._datastore.get_service_data_pool()
            for k, v in data_pool.items():
                self._logger.debug(f" - {k} : \t{v}")
            return data_pool
