#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.error_pool.error import InvalidInputException
from api.workflow.error_pool.error import NotDefinedWorkflowMetaException
from api.workflow.service.task.task_load_service import TaskLoadService


class ActionPlanningService:
    def __init__(self, logger, meta_pack, datastore):
        self._logger = logger
        self._meta_pack = meta_pack
        self._datastore = datastore
        self._taskstore = TaskLoadService(logger, meta_pack)

    def _gen_task_graph_for_from(self, base_graph, from_service_id, count=0):
        count += 1
        space = "\t" * count
        task_graph = {}
        self._logger.debug(f"{space}@[{count}] < from: {from_service_id} >")
        next_service_ids = base_graph.get(from_service_id)

        self._logger.debug(f"{space} [{count}] # Step 0: find child nodes - {next_service_ids}")
        if not next_service_ids and count == 1:
            self._logger.debug(f"{space} [{count}] # Step -1")
            raise InvalidInputException
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
        self._logger.debug(f"{space}@[{count}] < FROM: {from_service_id} -> END: {to_service_id} >")
        self._logger.debug(f"{space} [{count}] # Step 0: check end nodes ")
        if from_service_id == to_service_id:
            task_graph[from_service_id] = []
            return task_graph

        next_service_ids = base_graph.get(from_service_id)
        self._logger.debug(f"{space} [{count}] # Step 1: {from_service_id} has child nodes - {next_service_ids}")

        if not next_service_ids:
            self._logger.debug(f"{space} [{count}] # Step -1")
            task_graph[from_service_id] = []
            return task_graph

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
        forward_graph = self._meta_pack.get('forward_graph')
        backward_graph = self._meta_pack.get('backward_graph')

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

    def gen_action_backward_graph_service(self, forward_graph):
        act_backward_graph = dict()
        for service_id, target_list in forward_graph.items():
            for forward_service_id in target_list:
                if service_id == 'ENTRY':
                    act_backward_graph[forward_service_id] = []
                    continue
                if forward_service_id in act_backward_graph.keys():
                    act_backward_graph[forward_service_id].append(service_id)
                else:
                    act_backward_graph[forward_service_id] = [service_id]
        return act_backward_graph

    def gen_start_nodes_service(self, forward_graph):
        if "ENTRY" in forward_graph.keys():
            act_start_nodes = forward_graph.get('ENTRY')
        else:
            all_nodes = set(forward_graph.keys())
            reachable_nodes = set()
            for node_id in forward_graph:
                reachable_nodes.update(forward_graph[node_id])
            act_start_nodes = all_nodes - reachable_nodes
            sorted(list(act_start_nodes))
        return act_start_nodes

    def gen_end_nodes_service(self, backward_graph):
        act_end_nodes = self.gen_start_nodes_service(backward_graph)
        sorted(list(act_end_nodes))
        return act_end_nodes

    def gen_action_edges_param_map(self, start_nodes, request_params):
        act_edges_param_map = self._meta_pack.get('edges_param_map')
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
        if "ENTRY" in act_service_ids:
            act_service_ids.remove('ENTRY')
        act_service_ids.extend(list(backward_graph.keys()))
        act_service_ids = list(set(act_service_ids))
        return act_service_ids

    def gen_action_tasks(self, action_service_ids):
        task_map = self._taskstore.gen_active_tasks_service(action_service_ids)
        return task_map

    def _vaild_meta(self, action_meta_pack):
        if not action_meta_pack.get('start_nodes'):
            raise NotDefinedWorkflowMetaException

    def _vaild_params(self, act_start_nodes, params):
        action_meta_pack = self._meta_pack
        service_pool = action_meta_pack.get('service_pool')
        for act_start_node in act_start_nodes:
            service_node = service_pool.get(act_start_node)
            node_params = service_node.get('params')
            if not node_params:
                continue
            if not isinstance(params, dict) or not params:
                for node_param in node_params:
                    is_required = node_param.get('required')
                    param_name = node_param.get('key')
                    if is_required:
                        raise InvalidInputException

    def gen_action_meta_pack(self, start_node, end_node, params):
        try:
            action_meta_pack = self._meta_pack
            self._vaild_meta(action_meta_pack)

            self._logger.info(f" # Step 1. Forward Graph")
            act_forward_graph = self.gen_action_forward_graph_service(start_node, end_node)
            self._logger.debug(f"  act_forward_graph: {act_forward_graph}")

            self._logger.info(f" # Step 2. Backward Graph")
            act_backward_graph = self.gen_action_backward_graph_service(act_forward_graph)
            self._logger.debug(f"  act_backward_graph: {act_backward_graph}")

            self._logger.info(f" # Step 3. Start Service Node")
            act_start_nodes = self.gen_start_nodes_service(act_forward_graph)
            self._logger.debug(f"  start nodes: {act_start_nodes}")
            self._vaild_params(act_start_nodes, params)

            self._logger.info(f" # Step 4. End Service Node")
            act_end_nodes = self.gen_end_nodes_service(act_backward_graph)
            self._logger.debug(f"  end nodes: {act_end_nodes}")

            self._logger.info(f" # Step 5. Extract task-edge_param_map")
            act_edges_param_map = self.gen_action_edges_param_map(act_start_nodes, params)
            self._print_map(act_edges_param_map)

            self._logger.info(f" # Step 6. Generate Active Tasks")
            action_service_ids = self.gen_action_service_ids(act_forward_graph, act_backward_graph)
            act_task_map = self.gen_action_tasks(action_service_ids)
            self._datastore.set_task_map_service(act_task_map)

            action_meta_pack['act_forward_graph'] = act_forward_graph
            action_meta_pack['act_backward_graph'] = act_backward_graph
            action_meta_pack['act_start_nodes'] = act_start_nodes
            action_meta_pack['act_end_nodes'] = act_end_nodes
            action_meta_pack['act_edges_param_map'] = act_edges_param_map
            action_meta_pack['act_task_map'] = act_task_map
            self._print_map(action_meta_pack)
            return action_meta_pack
        except NotDefinedWorkflowMetaException as e:
            self._logger.error(e)
            raise NotDefinedWorkflowMetaException
        except InvalidInputException as e:
            self._logger.warn(e)
            raise AttributeError
        except AttributeError as e:
            self._logger.error(e)
            raise AttributeError
        except Exception as e:
            self._logger.error(e)

    def _print_map(self, data_map):
        for k, v in data_map.items():
            self._logger.debug(f"{k} : {v}")