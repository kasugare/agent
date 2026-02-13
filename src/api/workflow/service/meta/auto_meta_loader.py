#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.conf_serving import getRecipeDir, getRecipeFile
from api.workflow.service.meta.wf_meta_parser import WorkflowMetaParser
from api.workflow.access.meta.meta_file_access import MetaFileAccess
from api.workflow.service.meta.meta_store_service import MetaStoreService
from typing import Any
from watchfiles import awatch
import traceback
import threading
import asyncio
import os


class AutoMetaLoader:
    def __init__(self, logger):
        self._logger = logger
        self._auto_loader()

    def _auto_loader(self, dirpath: str = None, filename: str = None) -> None:
        def run_event_loop(dirpath: str, filename: str) -> None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._task = loop.create_task(self._startup_event(dirpath, filename))
            loop.run_forever()

        if not dirpath:
            dirpath = getRecipeDir()
        if not filename:
            filename = getRecipeFile()
        thread = threading.Thread(target=run_event_loop, daemon=True, args=(dirpath, filename))
        thread.start()

    async def _startup_event(self, dirpath, filename):
        asyncio.create_task(self._watch_recipe(dirpath, filename))

    async def _watch_recipe(self, dirpath: str, filename: str) -> Any:
        try:
            self._logger.debug(f"watch changeable recipe file: {dirpath}/{filename}")
            wf_filepath = os.path.join(dirpath, filename)
            async for changes in awatch(wf_filepath):
                try:
                    await self._sync_workflow_meta()
                except Exception as e:
                    self._logger.error(traceback.format_exc())
                    self._logger.warn(f"Not ready {wf_filepath} file")
        except Exception as e:
            print(traceback.format_exc())

    async def _sync_workflow_meta(self):
        filed_wf_meta = MetaFileAccess(self._logger).load_wf_meta_on_file()
        if not filed_wf_meta:
            return

        meta_parser = WorkflowMetaParser(self._logger)
        filed_meta_pack = meta_parser.parse_wf_meta(filed_wf_meta)
        if not filed_meta_pack:
            self._logger.error("Not existed meta")
            return

        wf_id = filed_meta_pack.get('workflow_id')
        metastore = MetaStoreService(self._logger, wf_id)
        # metastore = self._meta_service_pool.get_metastore(wf_id)

        if metastore:
            current_wf_meta = metastore.get_wf_meta_service()
            if current_wf_meta != filed_wf_meta:
                self._logger.debug("# SYNC UPDATE")
                metastore.set_meta_pack_service(filed_meta_pack)
                self._logger.debug(filed_wf_meta)
            else:
                return
        else:
            # _, metastore = self._meta_service_pool.create_pool(wf_id)
            metastore.set_meta_pack_service(filed_meta_pack)

    def init_workflow_meta(self):
        wf_meta = MetaFileAccess(self._logger).load_wf_meta_on_file()
        if not wf_meta:
            return
        meta_parser = WorkflowMetaParser(self._logger)
        meta_pack = meta_parser.parse_wf_meta(wf_meta)
        wf_id = meta_pack.get("workflow_id")
        metastore = MetaStoreService(self._logger, wf_id)

        # _, metastore = self._meta_service_pool.create_pool(wf_id)
        metastore.set_meta_pack_service(meta_pack)
