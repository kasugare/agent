#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.access.execute.start_executor import StartExecutor
from api.workflow.access.execute.end_executor import EndExecutor
from api.workflow.access.execute.api_executor import ApiExecutor
from api.workflow.control.execute.task import Task


class TaskGenerator:
    def __init__(self, logger, datastore):
        self._logger = logger
        self._datastore = datastore
        self._meta_pack = datastore.get_meta_pack()

    def get_edge_info(self, edge_id):
        edges_info = self._meta_pack.get('edges_info')
        edge_info = edges_info.get(edge_id)
        return edge_info

    def get_node_info(self, service_id):
        node_pool = self._meta_pack.get('service_pool')
        node_info = node_pool.get(service_id)
        return node_info

    def get_next_service_ids(self, service_id):
        edges_grape = self._meta_pack['edges_grape']
        next_service_ids = edges_grape.get(service_id)
        return next_service_ids

    def extract_api_info(self, service_id):
        node_info = self.get_node_info(service_id)
        url_info = {
            'url': node_info.get('url'),
            'method': node_info.get('method'),
            'header': node_info.get('header'),
            'body': node_info.get('body')
        }
        return url_info

    def get_start_nodes(self):
        start_nodes = self._meta_pack['start_nodes']
        return start_nodes

    def prepare_next_job(self, curr_service_id, next_service_id):
        edge_id = f"{curr_service_id}-{next_service_id}"
        self._logger.debug(f" # Step 1. edge_id: {edge_id}")

        edge_info = self.get_edge_info(edge_id)  ## 미리 셋팅
        self._logger.debug("f # Step 2. edge_info")
        for k, v in edge_info.items():
            print(" - ", k, ":", v)

        self._logger.debug("f # Step 3. extract data_mapper")
        data_mapper = edge_info.get('data_mapper')
        for map_info in data_mapper:
            print(f" - {map_info}")

        #
        # self._logger.debug(f" # Step 5. edge_info")
        # # self._logger.warn(f"    - {edge_info}")
        # tar_service_id = edge_info.get('target')
        #
        # self._logger.debug(f" # Step 6. generate target_params: {tar_service_id}") ## 실행시 저장
        # tar_params = self._datastore.get_next_service_params(edge_info)
        # # self._logger.debug(f"   - {tar_params}")
        #
        # self._logger.debug(f" # Step 7. Save target params") ## 실행시 저장
        # self._datastore.set_service_params(tar_service_id, tar_params)
        #
        # self._logger.debug(f" # Step 8. get service url info") ## 미리 셋팅
        # tar_api_url_info = self.extract_api_info(tar_service_id)
        # tar_api_url_info['params'] = tar_params  ## 실행시 셋팅
        # # self._logger.debug(f"   - {tar_api_url_info}")
        #
        # self._logger.debug(f" # Step 9. set task Queue")
        # print(tar_api_url_info)

    def make_tasks(self):
        self._logger.info("=" * 170)
        start_service_ids = self.get_start_nodes()
        for curr_service_id in start_service_ids:
            print(curr_service_id)
            next_service_ids = self.get_next_service_ids(curr_service_id)
            print(f"{curr_service_id} : {next_service_ids}")
            for next_service_id in next_service_ids:
                self.prepare_next_job(curr_service_id, next_service_id)

