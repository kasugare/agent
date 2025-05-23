#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List, Any
import traceback
import asyncio
import aiohttp


class ApiExecutor:
    def __init__(self, logger):
        self._logger = logger

    async def _call_api(self, end_point: Dict) -> Dict:
        async with aiohttp.ClientSession() as session:
            url = end_point.get('url')
            params = end_point.get('params')
            async with session.post(url, json=params) as response:
                try:
                    if response.status >= 400:
                        error_text = await response.text()
                        print(error_text)
                        raise Exception(f"API call failed with status {response}")

                    result = {"status": "success", "result": await response.json()}
                    self._logger.debug(f" - task completed successfully: {result}")
                except Exception as e:
                    self._logger.error(f"Workflow execution error_pool: {str(e)}\n{traceback.format_exc()}")
                    result = {"status": "error_pool", "error_pool": str(e)}
                return result

    def run_api(self, end_point):
        self._logger.info(f"[Executor] Call API: {end_point}")
        result = asyncio.run(self._call_api(end_point))
        return result