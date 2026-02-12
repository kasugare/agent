#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.conf_system import getLockDir
from common.conf_serving import getRecipeDir, getRecipeFile
from api.workflow.access.meta.file_lock import FileLock
from typing import Dict
import traceback
import json
import os


class MetaFileAccess:
    def __init__(self, logger, meta_dir: str = "recipe"):
        self._logger = logger
        self._dirpath = getRecipeDir()
        self._filename = getRecipeFile()
        self._lock_filepath = f"{getLockDir()}.stt_wf_meta.lock"

    def _get_wf_file_info(self, dirpath, filename):
        if not dirpath:
            dirpath = self._dirpath
        if not filename:
            filename = self._filename
        return dirpath, filename

    def load_wf_meta_on_file(self, dirpath:str = None, filename: str = None) -> Dict:
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
            self._logger.error(f"Can not found DAG meta file: {filename}")
            raise Exception(f"Can not found DAG meta: {filename}")

        except json.JSONDecodeError as e:
            traceback.format_exc(e)
            self._logger.error(f"wrong json format, decode error: {filename}")
            raise Exception(f"wrong json format, decode error: {filename}")

        except ValueError as e:
            self._logger.error(e)
            raise Exception(f"not exist required dag fields: {filename}")
        return dag_info

    def save_wf_meta_on_file(self, wf_meta: Dict, dirpath: str = None, filename: str = None) -> None:
        if not dirpath:
            dirpath = self._dirpath
        if not filename:
            filename = self._filename

        with FileLock(self._lock_filepath):
            try:
                if not os.path.exists(dirpath):
                    os.makedirs(dirpath)
                filepath = os.path.join(dirpath, filename)
                with open(filepath, 'w') as fd:
                    json.dump(wf_meta, fd, indent=2)
            except Exception as e:
                self._logger.error(e)
