#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List, Any
import traceback
import asyncio
import aiohttp


class ApiExecutor:
    def __init__(self, logger, url, method, header, body):
        self._logger = logger
        self._url = url
        self._method = method
        self._header = header
        self._body = body
        self._env_params = {}
        self._params = None

    def set_env(self, env_params):
        self._env_params = env_params

    def set_url(self, url):
        self._url = url

    def get_url(self):
        return self._url

    def set_params(self, params):
        self._params = params

    def get_params(self):
        if not self._params:
            return {}
        return self._params

    def set_body(self, body):
        self._body = body

    def get_body(self):
        return self._body

    def set_header(self, header):
        self._header = header

    def get_header(self):
        return self._header

    async def _call_api(self) -> Dict:
        async with aiohttp.ClientSession() as session:
            async with session.post(self.get_url(), json=self.get_params()) as response:
                try:
                    if response.status >= 400:
                        error_text = await response.text()
                        self._logger.error(error_text)
                        raise Exception(f"API call failed with status {response}")
                    result = {"status": "success", "result": await response.json()}
                    self._logger.debug(f" - task completed successfully: {result}")
                except Exception as e:
                    self._logger.error(f"Workflow execution error_pool: {str(e)}\n{traceback.format_exc()}")
                    result = {"status": "error_pool", "error_pool": str(e)}
                    raise Exception
                return result

    def run(self, params):
        self._logger.info(f"[Executor] Call API: {params}")
        self.set_params(params)
        result = asyncio.run(self._call_api())
        result_map = result.get('result')
        return result_map