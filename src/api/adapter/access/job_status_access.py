#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.conf_adapter import getRemoteEngineUrl
from api.adapter.access.connector.exteranl_api_requester import ExternalApiRequester
from typing import Dict
import asyncio


class JobStatusAccess(ExternalApiRequester):
    def __init__(self, logger):
        super().__init__(logger)
        self._logger = logger
        self._timeout = None

    def set_timeout(self, timeout):
        self._timeout = timeout

    async def get_working_state_access(self) -> Dict:
        try:
            engine_url = getRemoteEngineUrl()
            result = await asyncio.create_task(
                self.call_external_api(
                    base_url=str(engine_url),
                    path="/api/v1/workflow/working_state",
                    method="GET",
                    headers={
                        "Content-Type": "application/json"
                    }
                )
            )
        except Exception as e:
            self._logger.error(e)
            result = {}
        return result

    async def get_job_status_detail_access(self, job_id: str) -> Dict:
        try:
            engine_url = getRemoteEngineUrl()
            result = await asyncio.create_task(
                self.call_external_api(
                    base_url=engine_url,
                    path="/api/v1/workflow/job_state",
                    method="GET",
                    headers={
                        "Content-Type": "application/json",
                        "secret_key": "",
                        "job_id": f"{job_id}",
                    }
                )
            )
        except Exception as e:
            self._logger.error(e)
            result = {}
        return result