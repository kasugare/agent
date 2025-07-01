#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.protocol.protocol_message import gen_task_order
from api.workflow.control.execute.worflow_navigator import WorkflowNavigator
from api.workflow.access.execute.api_executor import ApiExecutor
from multiprocessing import Queue
import threading


class ExecutionFlowController(WorkflowNavigator):
    def __init__(self, logger, data_service, job_Q):
        super().__init__(logger, data_service)

        self._logger = logger
        self._data_service = data_service
        self._job_Q = job_Q
        self._job_status = {}

    def _print_running_task(self, task_order):
        order_sheet = task_order.get('orders')
        service_id = task_order.get('service_id')
        end_point = order_sheet.get('endpoint')
        task_meta = order_sheet.get('task_meta')
        edge_id = task_meta.get('edge_id')
        edge_info = task_meta.get('edge_info')
        self._logger.warn(f"  RUN: < edge_id: {edge_id} >")
        self._logger.warn(f"  RUN: service_id: {service_id}")
        self._logger.warn(f"  RUN: end_point: {end_point}")

    def request_execution(self, task_order):
        self._job_Q.put_nowait(task_order)

    def _run_executor(self, task_order):
        self._logger.debug(f" # Step 10. Call API")
        self._print_running_task(task_order)
        order_sheet = task_order.get('orders')
        service_id = task_order.get('service_id')
        end_point = order_sheet.get('endpoint')

        self.set_job_status(service_id, status='running')

        executor = ApiExecutor(self._logger)

        output_result = executor.run(end_point)
        result = output_result.get('result')
        self.set_job_status(service_id, status='done')
        task_order['output'] = result

        self._job_Q.put_nowait(task_order)

    def run_exec_handler(self):
        def start_job(task_map):
            thread = threading.Thread(target=self._run_executor, args=(task_map,))
            thread.start()

        while True:
            task_order = self._job_Q.get()
            service_id = task_order.get('service_id')
            status = self.get_job_status(service_id)

            if status == 'idle':
                self._logger.error(f"[IDLE --> WAIT] - {service_id}")
                self.set_job_status(service_id, status='wait')
                is_finished_prev = self.check_finished_prev_services(service_id)
                if is_finished_prev:
                    self.request_execution(task_order)
            elif status == 'wait':
                self._logger.error(f"[WAIT --> RUNNING] - {service_id}")
                role = self.get_service_role(service_id)
                if role.lower() == 'start':
                    task_order['output'] = self._data_service.get_service_params(service_id)
                    self.set_job_status(service_id, status='done')
                    self._job_Q.put_nowait(task_order)
                elif role == 'end':
                    task_order['output'] = self._data_service.get_service_params(service_id)
                    self.set_job_status(service_id, status='done')
                    self._job_Q.put_nowait(task_order)
                elif role == 'aggregation':
                    start_job(task_order)
                else:
                    start_job(task_order)
            elif status == 'running':
                pass
            elif status == 'done':
                self._logger.error(f"[RUNNING --> DONE] - {service_id}")
                result = task_order.get('output')
                self._logger.error(f" - {service_id} : {result}")

                self._data_service.set_service_result(service_id, result)
                next_service_ids = self.get_next_nodes(service_id)
                if not next_service_ids:
                    self.print_data_pool()
                    continue
                for next_service_id in next_service_ids:
                    self._logger.error(f"[DONE --> NEXT] - {service_id} : {next_service_id}")
                    is_finished_prev = self.check_finished_prev_services(next_service_id)
                    if is_finished_prev:
                        task_order = self.prepare_next_job(service_id, next_service_id)
                        self.request_execution(task_order)
            self.print_service()
        return self._result_set

    def do_process(self, request_params):
        self.init_job_status()
        start_nodes = self.get_start_nodes()
        for service_id in start_nodes:
            self._logger.debug(f" # Step 1. service_id: {service_id}")
            self.set_init_params(service_id, request_params)
            task_order = gen_task_order(None, service_id, None, None, None)
            self.set_job_status(service_id, status='wait')
            self.request_execution(task_order)

        thread = threading.Thread(target=self.run_exec_handler, args=())
        thread.start()