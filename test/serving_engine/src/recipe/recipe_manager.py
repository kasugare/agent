#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List, Any
from pathlib import Path
import traceback
import json
import os

REQUIRED_DAG_FIELDS = ['nodes', 'edges']
REQUIRED_NODE_FIELDS = ['id', 'type', 'dependencies', 'next']
REQUIRED_EDGE_FIELDS = ['source', 'target']


class WorkflowDAGManager:
    def __init__(self, logger, config_dir: str = "config"):
        self._logger = logger
        self.loader = DAGLoader(config_dir)
        self.loaded_dags: Dict[str, Dict] = {}

    def get_dag(self, dag_id: str, refresh: bool = False) -> Dict:
        """DAG 설정 가져오기 (캐시 지원)"""
        if refresh or dag_id not in self.loaded_dags:
            self.loaded_dags[dag_id] = self.loader.load_dag(dag_id)
        return self.loaded_dags[dag_id]

    def reload_all(self) -> None:
        """모든 로드된 DAG 새로고침"""
        for dag_id in list(self.loaded_dags.keys()):
            self.get_dag(dag_id, refresh=True)

    def get_available_dags(self) -> list:
        """사용 가능한 모든 DAG 파일 목록 반환"""
        path = Path(self.loader.config_dir)
        return [f.stem for f in path.glob("*.json")]


class DAGLoader:
    def __init__(self, logger, config_dir: str = "config"):
        self._logger = logger
        self._config_dir = config_dir

    def load_dag(self, filename: str) -> Dict:
        self._logger.info("TEST")
        self._logger.debug(f"Step 1. load DAG from json file: {filename}")
        try:
            file_path = self. _get_file_path(filename)
            with open(file_path, 'r', encoding='utf-8') as fd:
                dag_info = json.load(fd)
            self._validate_dag(dag_info)

        except FileNotFoundError as e:
            traceback.format_exc(e)
            self._logger.error(f"Can not found DAG config file: {filename}")
            raise Exception(f"Can not found DAG config: {filename}")

        except json.JSONDecodeError as e:
            traceback.format_exc(e)
            self._logger.error(f"wrong json format, decode error: {filename}")
            raise Exception(f"wrong json format, decode error: {filename}")

        except ValueError as e:
            # traceback.format_exc(e)
            self._logger.error(e)
            raise Exception(f"not exist required dag fields: {filename}")
        return dag_info

    def _get_file_path(self, filename: str) -> str:
        if not filename.endswith('.json'):
            filename = f"{filename}.json"
        file_path = os.path.join(self._config_dir, filename)
        return file_path

    def _validate_dag(self, dag_info: Dict) -> None:
        self._logger.debug("# check validation - DAG")

        self._logger.debug(" - check required DAG fields")
        for field in REQUIRED_DAG_FIELDS:
            if field not in dag_info:
                self._logger.error(f"Not exist required filed: {field}")
                raise ValueError(f"Not exist required filed: {field}")

        self._logger.debug(" - check required node fields")
        for node_id, node in dag_info['nodes'].items():
            for field in REQUIRED_NODE_FIELDS:
                if field not in node:
                    self._logger.error(f"Not exist required node filed: {field}")
                    raise ValueError(f"Not exist required node filed: {field}")

        self._logger.debug(" - check required edges fields")
        for edge in dag_info['edges']:
            for req_edge in REQUIRED_EDGE_FIELDS:
                if req_edge not in edge.keys():
                    self._logger.critical(edge)
                    self._logger.error(f"Not exist required edge filed: {edge}")
                    raise ValueError(f"Not exist required edge filed: {edge}")
