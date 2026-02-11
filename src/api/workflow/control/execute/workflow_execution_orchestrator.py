#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.control.execute.task_state import TaskState
from api.workflow.control.execute.env_template import AutoTemplateRenderer
from api.workflow.control.execute.workflow_helper import WorkflowHelper
from api.workflow.protocol.protocol_message import SYS_NODE_STATUS
from api.workflow.error_pool.error import ExceedExecutionRetryError
from jinja2 import Template, meta, Environment
from multiprocessing import Queue
from threading import Thread
import traceback
import time


class WorkflowExecutionOrchestrator(WorkflowHelper):
    def __init__(self, logger, store_pack, meta_pack, stream_Q=None):
        super().__init__(logger, store_pack, meta_pack)
        self._logger = logger
        self._store_pack = store_pack
        self._datastore = store_pack.get('datastore', {})
        self._taskstore = store_pack.get('taskstore', {})
        self._meta_pack = meta_pack
        self._job_Q = Queue()
        self._stream_Q = stream_Q

    def _set_start_jobs(self, request_params):
        start_service_ids = self._get_start_nodes()
        for start_service_id in start_service_ids:
            self._datastore.set_service_params_service(start_service_id, request_params)
            self._job_Q.put_nowait(start_service_id)

    def _execute_task(self, task):
        task.execute()
        service_id = task.get_service_id()
        self._job_Q.put_nowait(service_id)

    def _send_status(self, request_id, service_id, task):
        splited_service_id = service_id.split('.')
        node_id = splited_service_id[0]
        service_name = splited_service_id[1]

        task_state = task.get_state()
        task_params = task.get_params()
        task_results = task.get_result()
        task_envs = task.get_env_params()
        task_error = task.get_error()

        status = str(task_state).split('.')[1]
        status_message = SYS_NODE_STATUS(request_id, node_id, service_name, status, int(time.time()),
                            params=task_params, results=task_results, envs=task_envs, error=task_error)
        self._stream_Q.put_nowait(status_message)
        time.sleep(0.01)

    def _timeout(self, timeout):
        time.sleep(timeout)
        self._job_Q.put_nowait("SIGTERM")

    def _run_pending(self, service_id):
        runnable = self._check_prev_task_compledted(service_id)
        self._logger.debug(f"   L RUNNABLE: {service_id} : {runnable}")
        if runnable:
            self._set_task_state(service_id, TaskState.SCHEDULED)
            self._job_Q.put_nowait(service_id)

    def _run_scheduled(self, service_id):
        self._set_task_state(service_id, TaskState.QUEUED)
        self._job_Q.put_nowait(service_id)

    def _run_queue(self, service_id, task_map, task):
        runnable = True
        prev_service_ids = self._get_prev_service_ids(service_id)
        if prev_service_ids:
            for prev_service_id in prev_service_ids:
                prev_task = task_map.get(prev_service_id)
                if prev_task.get_state() not in [TaskState.COMPLETED, TaskState.SKIPPED]:
                    runnable = False
                    return False
        else:
            runnable = True
        self._logger.debug(f"   L RUNNABLE: {service_id} : {runnable}")

        if runnable:
            env_params = self._get_envs(service_id)
            asset_params = self._get_assets(service_id)
            self._set_env_params(service_id, env_params)
            self._set_asset_params(service_id, asset_params)

            task_role = task.get_role()
            func_params = {}

            self._logger.debug(f" - ROLE: {service_id} - {task_role}")
            if task_role == 'generation':
                func_params = self._get_params(service_id)
                param_value = self._extract_forced_param_value(service_id, "messages")
                func_params['messages'] = param_value
            elif task_role == 'aggregation':
                func_params = self._get_aggr_params(service_id)
            elif task_role == 'condition':
                edges_info = self._meta_pack.get('edges_info', {})
                edge_ids = self._get_edge_ids_by_service_id(service_id)
                if edge_ids:
                    edge_id = edge_ids[0]
                else:
                    return True
                edge_meta = edges_info.get(edge_id)
                target_handler = edge_meta.get('target_handler', {})
                handler_type = target_handler.get('type')
                if handler_type == 'conditional':
                    condition_map = target_handler.get("conditions", {})
                    condition_branches = condition_map.get('branches', [])
                    for condition_branch in condition_branches:
                        branch_rules = condition_branch.get('rules', [])
                        for rule_map in branch_rules:
                            param_id = rule_map.get('variable')
                            rule_map['variable'] = self._datastore.get_output_value(param_id)
                            if rule_map.get("refer_type") == 'indirect':
                                value_id = rule_map.get('value')
                                if not value_id:
                                    continue
                                rule_map['value'] = self._datastore.get_output_value(value_id)
                    self._set_handler(service_id, target_handler)
            else:
                func_params = self._get_params(service_id)
            self._set_params(service_id, func_params)
            self._set_task_state(service_id, TaskState.RUNNING)
            self._job_Q.put_nowait(service_id)
            return True

    def _run_execution(self, task):
        executor = Thread(target=self._execute_task, args=(task,), daemon=True)
        executor.start()

    def _run_task_completed(self, service_id, task_map, task):
        task_result = task.get_result()
        customed_task_result = self._result_mapper(service_id, task_result)
        self._set_result(service_id, customed_task_result)
        self._datastore.set_service_result_service(service_id, customed_task_result)

        task_role = task.get_role()
        if task_role == 'condition':
            self._logger.debug(f"   L RESULT: {customed_task_result}")
            actions = customed_task_result.get('actions', [])
            execution_service_ids = []
            for action_map in actions:
                if action_map.get('action') == 'execution':
                    execution_service_ids.append(action_map.get('value'))

            edges_graph = self._meta_pack['act_forward_graph']
            next_service_ids = edges_graph.get(service_id)
            skip_target_service_ids = list(set(next_service_ids).difference(set(execution_service_ids)))
            self._set_action_skip_nodes(service_id, skip_target_service_ids)
            self._set_blocked_nodes(service_id)
        else:
            next_service_ids = self._get_next_service_ids(service_id)

        for next_service_id in next_service_ids:
            self._job_Q.put_nowait(next_service_id)

    def _run_exec_handler(self, task_map, request_id=None):
        result = None
        start_ts = time.time()
        while True:
            try:
                self._logger.debug("<<< Ready: Job Q >>>")
                service_id = self._job_Q.get()
                if service_id == "SIGTERM":
                    self._logger.error("Exit process")
                    break
                if service_id == 'None':
                    continue

                task = task_map.get(service_id)
                task_state = task.get_state()
                self._set_task_state(service_id, task_state)

                if self._stream_Q:
                    self._send_status(request_id, service_id, task)

                if task_state in [TaskState.PENDING]:
                    self._logger.info(f" - Step 1. [PENDING  ] wait order to run: {service_id}")
                    self._run_pending(service_id)

                elif task_state in [TaskState.SCHEDULED]:
                    self._logger.info(f" - Step 2. [SCHEDULED] prepared service resources: {service_id}")
                    self._run_scheduled(service_id)

                elif task_state in [TaskState.QUEUED]:
                    self._logger.info(f" - Step 3. [QUEUED   ] aggregation params and run: {service_id}")
                    is_runnable = self._run_queue(service_id, task_map, task)
                    if not is_runnable:
                        break

                elif task_state in [TaskState.RUNNING, TaskState.RETRYING]:
                    self._logger.info(f" - Step 4. [RUNNING] run task execution : {service_id}")
                    self._run_execution(task)

                elif task_state in [TaskState.COMPLETED]:
                    self._logger.info(f" - Step 5. [COMPLETED] done task execution : {service_id}")
                    self._run_task_completed(service_id, task_map, task)
                    if self._check_all_completed(task_map):
                        result = self._get_job_result(task_map)
                        break

                elif task_state in [TaskState.TIMEOUT]:
                    self._logger.info(f" - Step 6. [TIMEOUT   ] task timeout : {service_id}")
                    self._show_task(task_map)
                    break

                elif task_state in [TaskState.FAILED]:
                    self._logger.info(f" - Step 7. [FAILED   ] job failed : {service_id}")
                    self._show_task(task_map)
                    break

                elif task_state in [TaskState.PAUSED]:
                    self._logger.info(f" - Step 8. [PAUSED   ] paused task by user : {service_id}")
                    break

                elif task_state in [TaskState.STOPPED]:
                    self._logger.warn(f" - Step 9. [STOP     ] stop task by user : {service_id}")
                    break

                elif task_state in [TaskState.SKIPPED]:
                    self._logger.info(f" - Step 10. [SKIPPED  ] skipped task: {service_id}")

                elif task_state in [TaskState.BLOCKED]:
                    self._logger.info(f" - Step 11. [BLOCKED  ] blocked task: {service_id}")
                    break
                else:
                    break
                self._show_task(task_map)
            except ExceedExecutionRetryError as e:
                break

            except Exception as e:
                self._logger.error(e)
                self._logger.error(traceback.print_exc())
                break

        end_ts = time.time()
        duration = "%0.2f" %(end_ts - start_ts)
        self._logger.info(f"--- # Request Job Completed, Duration: {duration}s ---")
        self._logger.debug(f" - Result: {result}")
        self._show_task(task_map)
        return result

    def run_workflow(self, request_params):
        self._logger.debug(f" # user params: {request_params}")
        request_id = request_params.get('request_id')
        self._set_start_jobs(request_params)
        task_map = self._meta_pack.get('act_task_map')
        result = self._run_exec_handler(task_map, request_id)
        return result
