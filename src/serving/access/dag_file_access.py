#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.conf_system import getLockDir, getRecipeDir, getRecipeFile
from api.serving.access.file_lock import FileLock
from typing import Dict
import traceback
import json
import os


class DagFileAccess:
    def __init__(self, logger, config_dir: str = "config"):
        self._logger = logger
        self._config_dir = config_dir
        self._dirpath = getRecipeDir()
        self._filename = getRecipeFile()
        self._lock_filepath = f"{getLockDir()}.stt_wf_meta.lock"

    def _get_wf_file_info(self, dirpath, filename):
        if not dirpath:
            dirpath = self._dirpath
        if not filename:
            filename = self._filename
        return dirpath, filename

    def get_wf_config_on_file(self, dirpath:str = None, filename: str = None) -> str:
        dirpath, filename = self._get_wf_file_info(dirpath, filename)

        if not os.path.exists(dirpath):
            os.mkdir(dirpath)

        if not filename.endswith('.json'):
            filename = f"{filename}.json"
        filepath = os.path.join(dirpath, filename)

        dag_info = {}
        try:
            with FileLock(self._lock_filepath):
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as fd:
                        dag_info = json.load(fd)
                else:
                    os.makedirs(dirpath, exist_ok=True)
                    with open(filepath, 'w') as fd:
                        json.dump({}, fd, indent=2)
        except FileNotFoundError as e:
            traceback.format_exc(e)
            self._logger.error(f"Can not found DAG config file: {filename}")
            raise Exception(f"Can not found DAG config: {filename}")

        except json.JSONDecodeError as e:
            traceback.format_exc(e)
            self._logger.error(f"wrong json format, decode error: {filename}")
            raise Exception(f"wrong json format, decode error: {filename}")

        except ValueError as e:
            self._logger.error(e)
            raise Exception(f"not exist required dag fields: {filename}")
        return dag_info

    def set_wf_config_on_file(self, wf_config:Dict, dirpath:str = None, filename:str = None) -> None:
        dirpath, filename = self._get_wf_file_info(dirpath, filename)

        with FileLock(self._lock_filepath):
            if not os.path.exists(dirpath):
                os.mkdir(dirpath)
            filepath = os.path.join(dirpath, filename)
            with open(filepath, 'w') as fd:
                json.dump(wf_config, fd, indent=2)