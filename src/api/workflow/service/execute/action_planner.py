#!/usr/bin/env python
# -*- coding: utf-8 -*-

class ActionPlanningService:
    def __init__(self, logger, datastore, metastore, taskstore):
        self._logger = logger
        self._datastore = datastore
        self._metastore = metastore
        self._taskstore = taskstore

    def _gen_task_graph_for_from(self, base_graph, from_service_id, count=0):
        count += 1
        space = "\t" * count
        task_graph = {}
        self._logger.debug(f"{space}@[{count}] < from: {from_service_id} >")
        next_service_ids = base_graph.get(from_service_id)

        self._logger.debug(f"{space} [{count}] # Step 0: find child nodes - {next_service_ids}")
        if not next_service_ids and count == 1:
            self._logger.debug(f"{space} [{count}] # Step -1")
            return None
        elif not next_service_ids:
            task_graph[from_service_id] = []
            return task_graph

        self._logger.debug(f"{space} [{count}] # Step 1: Checking...")
        for next_service_id in next_service_ids:
            self._logger.debug(f"{space} [{count}] # Step 2: select and find next service - {next_service_id}")

            next_graph = self._gen_task_graph_for_from(base_graph, next_service_id, count)
            self._logger.debug(f"{space} [{count}] # Step 3: next_nodes: {next_graph}")
            if not next_graph:
                self._logger.debug(f"{space} [{count}] # Step 4: not exist next services")
                continue
            self._logger.debug(f"{space} [{count}] # Step 5: save next graph")
            task_graph.update(next_graph)

            if task_graph.get(from_service_id):
                self._logger.debug(f"{space} [{count}] # Step 6: Add on - {from_service_id}")
                task_graph[from_service_id].append(next_service_id)
            else:
                self._logger.debug(f"{space} [{count}] # Step 7: NEW - {from_service_id}")
                task_graph[from_service_id] = [next_service_id]
        self._logger.debug(f"{space} [{count}] # Step 8: completed registration")
        return task_graph

    def _gen_task_graph(self, base_graph, from_service_id, to_service_id, count=0):
        count += 1
        space = "\t" * count
        task_graph = {}
        self._logger.debug(f"{space}@[{count}] < {from_service_id} -> {to_service_id} >")
        self._logger.debug(f"{space} [{count}] # Step 0: check end nodes ")
        if from_service_id == to_service_id:
            task_graph[from_service_id] = []
            return task_graph

        next_service_ids = base_graph.get(from_service_id)
        self._logger.debug(f"{space} [{count}] # Step 1: {from_service_id} has child nodes - {next_service_ids}")

        if not next_service_ids:
            self._logger.debug(f"{space} [{count}] # Step -1")
            return None

        for next_service_id in next_service_ids:
            self._logger.debug(f"{space} [{count}] # Step 2: select and find next service - {next_service_id}")
            next_graph = self._gen_task_graph(base_graph, next_service_id, to_service_id, count)

            self._logger.debug(f"{space} [{count}] # Step 3: {next_graph}")
            if not next_graph:
                self._logger.debug(f"{space} [{count}] # Step 4: not exist next services")
                continue

            self._logger.debug(f"{space} [{count}] # Step 5: update found graph to next graph")
            task_graph.update(next_graph)

            if task_graph.get(from_service_id):
                self._logger.debug(f"{space} [{count}] # Step 6: Add on - {from_service_id}")
                task_graph[from_service_id].append(next_service_id)
            else:
                self._logger.debug(f"{space} [{count}] # Step 7: NEW- {from_service_id}")
                task_graph[from_service_id] = [next_service_id]

        self._logger.debug(f"{space} [{count}] # Step 8: completed registration")
        return task_graph

    def _cvt_service_range(self, from_service_id=None, to_service_id=None):
        forward_graph = self._datastore.get_forward_graph_meta_service()
        backward_graph = self._datastore.get_backward_graph_meta_service()

        if not from_service_id and not to_service_id:
            service_graph = forward_graph
        elif from_service_id and not to_service_id:
            service_graph = self._gen_task_graph_for_from(forward_graph, from_service_id)
        elif not from_service_id and to_service_id:
            service_graph = self._gen_task_graph_for_from(backward_graph, to_service_id)
        else:
            service_graph = self._gen_task_graph(forward_graph, from_service_id, to_service_id)
        return service_graph

    def gen_action_forward_graph_service(self, from_service_id, to_service_id):
        act_forward_graph = self._cvt_service_range(from_service_id, to_service_id)
        return act_forward_graph

    def gen_action_backward_graph_service(self, foreward_graph):
        act_backward_graph = self._metastore.reverse_forward_graph_service(foreward_graph)
        return act_backward_graph

    def gen_start_nodes_service(self, forward_graph):
        act_start_nodes = self._metastore.find_start_nodes_service(forward_graph)
        return act_start_nodes

    def gen_end_nodes_service(self, backward_graph):
        act_end_nodes = self._metastore.find_end_nodes_service(backward_graph)
        return act_end_nodes

    def gen_action_edges_param_map(self, start_nodes, request_params):
        act_edges_param_map = self._datastore.get_edges_param_map_service()
        if not request_params:
            return act_edges_param_map

        req_param_names = request_params.keys()
        for service_id in start_nodes:
            for task_edge_id, edge_param_map_list in act_edges_param_map.items():
                if task_edge_id.find(service_id) <= 0:
                    continue
                for edge_param_map in edge_param_map_list:
                    param_name = edge_param_map.get('key')
                    if param_name in req_param_names:
                        edge_param_map['refer_type'] = 'direct'
                        edge_param_map['value'] = f'I.{service_id}.{param_name}'
        return act_edges_param_map

    def gen_action_service_ids(self, forward_graph, backward_graph):
        if not forward_graph:
            return []
        act_service_ids = list(forward_graph.keys())
        act_service_ids.extend(list(backward_graph.keys()))
        act_service_ids = list(set(act_service_ids))
        return act_service_ids

    def gen_action_tasks(self, action_service_ids):
        task_map = self._taskstore.gen_active_tasks_service(action_service_ids)
        return task_map

    def gen_action_meta_pack(self, start_node, end_node, request):
        action_meta_pack = self._datastore.get_meta_pack_service()
        self._logger.info(f" # Step 1. Forward Graph")
        act_forward_graph = self.gen_action_forward_graph_service(start_node, end_node)
        self._print_map(act_forward_graph)

        self._logger.info(f" # Step 2. Backward Graph")
        act_backward_graph = self.gen_action_backward_graph_service(act_forward_graph)
        self._print_map(act_backward_graph)

        self._logger.info(f" # Step 3. Start Service Node")
        act_start_nodes = self.gen_start_nodes_service(act_forward_graph)
        self._logger.debug(f"  start nodes: {act_start_nodes}")

        self._logger.info(f" # Step 4. End Service Node")
        act_end_nodes = self.gen_end_nodes_service(act_backward_graph)
        self._logger.debug(f"  end nodes: {act_end_nodes}")

        self._logger.info(f" # Step 5. Extract task-edge_param_map")
        act_edges_param_map = self.gen_action_edges_param_map(act_start_nodes, request)
        self._print_map(act_edges_param_map)

        self._logger.info(f" # Step 6. Generate Active Tasks")
        action_service_ids = self.gen_action_service_ids(act_forward_graph, act_backward_graph)
        act_task_map = self.gen_action_tasks(action_service_ids)
        self._datastore.set_task_map_service(act_task_map)
        self._print_map(act_task_map)

        action_meta_pack['act_forward_graph'] = act_forward_graph
        action_meta_pack['act_backward_graph'] = act_backward_graph
        action_meta_pack['act_start_nodes'] = act_start_nodes
        action_meta_pack['act_end_nodes'] = act_end_nodes
        action_meta_pack['act_edges_param_map'] = act_edges_param_map
        action_meta_pack['act_task_map'] = act_task_map
        return action_meta_pack

    def _print_map(self, data_map):
        for k, v in data_map.items():
            self._logger.debug(f"{k} : {v}")