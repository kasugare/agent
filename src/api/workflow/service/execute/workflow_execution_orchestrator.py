#!/usr/bin/env python
# -*- coding: utf-8 -*-

# from api.workflow.control.execute.execution_flow_controller import ExecutionFlowController
from api.workflow.control.execute.task_generator import TaskGenerator
from api.workflow.control.execute.task_state import TaskState
from multiprocessing import Process, Queue
from threading import Thread
import traceback


class WorkflowExecutionOrchestrator:
    def __init__(self, logger, datastore, job_Q):
        self._logger = logger
        self._datastore = datastore
        self._meta_pack = datastore.get_meta_pack()

        self._job_Q = job_Q
        # self._flow_controller = ExecutionFlowController(logger, datastore, self._job_Q)
        self._task_generator = TaskGenerator(logger, datastore)

    def __del__(self):
        self._job_Q.put_nowait("SIGTERM")

    def _get_next_service_ids(self, service_id):
        edges_grape = self._meta_pack['edges_grape']
        next_service_ids = edges_grape.get(service_id)
        if not next_service_ids:
            next_service_ids = []
        return next_service_ids

    def _get_prev_service_ids(self, service_id):
        prev_edges_grape = self._meta_pack['prev_edges_grape']
        prev_service_ids = prev_edges_grape.get(service_id)
        return prev_service_ids

    def _get_start_nodes(self):
        start_nodes = self._meta_pack['start_nodes']
        return start_nodes

    def _get_end_nodes(self):
        end_nodes = self._meta_pack['end_nodes']
        return end_nodes

    def _set_job_Q_in_tasks(self, task_map):
        for service_id, task in task_map.items():
            task.set_job_Q(self._job_Q)

    def _set_start_jobs(self, request_params):
        start_service_ids = self._get_start_nodes()
        for start_service_id in start_service_ids:
            self._datastore.set_service_params(start_service_id, request_params)
            self._job_Q.put_nowait(start_service_id)

    def _check_all_completed(self, task_map):
        be_completed = True
        for k, task in task_map.items():
            if task.get_state() != TaskState.COMPLETED:
                be_completed = False
                break
        return be_completed

    def _run_exec_handler(self, task_map):
        result = None
        while True:
            try:
                self._logger.debug("<<< WAIT Q >>>")
                service_id = self._job_Q.get()
                if service_id == "TERMINATION":
                    print("DEL")
                    break
                task = task_map.get(service_id)
                task_state = task.get_state()
                self._logger.critical(f"# REQ: {service_id} - {task_state}")

                if task_state in [TaskState.PENDING]:
                    self._logger.debug(f" - Step 1. [PENDING  ] wait order to run: {service_id}")
                    task.set_state(TaskState.SCHEDULED)
                    self._job_Q.put_nowait(service_id)
                elif task_state in [TaskState.SCHEDULED]:
                    self._logger.debug(f" - Step 2. [SCHEDULED] prepared service resources: {service_id}")
                    task.set_state(TaskState.QUEUED)
                    self._job_Q.put_nowait(service_id)
                elif task_state in [TaskState.QUEUED]:
                    self._logger.debug(f" - Step 3. [QUEUED   ] aggregation params and run: {service_id}")
                    runnable = True
                    prev_service_ids = self._get_prev_service_ids(service_id)
                    if prev_service_ids:
                        for prev_service_id in prev_service_ids:
                            prev_task = task_map.get(prev_service_id)
                            if prev_task.get_state() not in [TaskState.COMPLETED, TaskState.SKIPPED]:
                                runnable = False
                    if runnable:
                        if not prev_service_ids:
                            params = self._datastore.get_start_service_params(service_id)
                        else:
                            params = self._datastore.get_service_params(service_id)
                        task.set_params(params)
                        task.set_state(TaskState.RUNNING)
                        self._job_Q.put_nowait(service_id)

                elif task_state in [TaskState.RUNNING]:
                    executor = Thread(target=task.execute, args=())
                    executor.start()

                elif task_state in [TaskState.COMPLETED]:
                    self._logger.debug(f" - Step 4. [COMPLETED] done task execution : {service_id}")
                    task_result = task.get_result()
                    self._datastore.set_service_result(service_id, task_result)
                    next_service_ids = self._get_next_service_ids(service_id)
                    for next_service_id in next_service_ids:
                        self._job_Q.put_nowait(next_service_id)

                    if self._check_all_completed(task_map):
                        end_service_ids = self._get_end_nodes()
                        for end_service_id in end_service_ids:
                            end_task = task_map.get(end_service_id)
                            result = end_task.get_result()
                        break

                elif task_state in [TaskState.FAILED]:
                    self._logger.debug(f" - Step 5. [FAILED   ] paused task by user : {service_id}")
                    self._show_task(task_map)
                    break
                elif task_state in [TaskState.PAUSED]:
                    self._logger.debug(f" - Step 6. [PAUSED   ] paused task by user : {service_id}")
                    break
                elif task_state in [TaskState.STOPPED]:
                    self._logger.debug(f" - Step 7. [STOP     ] stop task by user : {service_id}")
                    break
                elif task_state in [TaskState.SKIPPED]:
                    self._logger.debug(f" - Step 8. [SKIPPED  ] skipped task: {service_id}")
                    break
                elif task_state in [TaskState.BLOCKED]:
                    self._logger.debug(f" - Step 9. [BLOCKED  ] blocked task: {service_id}")
                    break
                else:
                    break
                self._show_task(task_map)
                # self._show_task_info(task)
            except Exception as e:
                self._logger.error(e)
                self._logger.error(traceback.print_exc())
                break
        return result

    def run_workflow(self, request_params):
        self._logger.critical(f" # user params: {request_params}")
        task_map = self._task_generator.make_tasks()
        self._set_job_Q_in_tasks(task_map)

        self._show_task(task_map)

        self._set_start_jobs(request_params)
        result = self._run_exec_handler(task_map)
        return result

    def _show_task(self, task_map):
        self._logger.warn(f"-" * 100)
        for service_id, task in task_map.items():
            self._logger.warn(f" - [{task.get_state()}] {service_id}")

    def _show_task_info(self, task):
        service_id = task.get_service_id()
        service_role = task.get_role()
        node_info = task.get_node_info()
        params = task.get_params()

        self._logger.debug(f" - service_id: {service_id}")
        self._logger.debug(f" - role: {service_role}")
        # self._logger.debug(f" - node_info: {node_info}")
        self._logger.debug(f" - params: {params}")
        self._logger.debug(f" - State: {task.get_state()}")
        self._logger.debug(f" - Error: {task.get_error()}")
        self._logger.debug(f" - Result: {task.get_result()}")
        # self._logger.debug(f" - Data: {service_io_data}")