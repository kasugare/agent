#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List, Any
import traceback
import asyncio
import aiohttp


class TaskExecutor:
    def __init__(self, logger):
        self._logger = logger

    async def _call_api(self, node_id: str, node_info: Dict) -> Dict:
        async with aiohttp.ClientSession() as session:
            api_info = node_info['config']['api']
            url = f"{api_info['url']}{api_info['route']}"

            params = {
                "node_id": node_id,
                "input_data": {"TEST": "test"},
                "request_id": "1234567890"
            }
            async with session.post(url, json=params) as response:
                try:
                    if response.status >= 400:
                        error_text = await response.text()
                        raise Exception(f"API call failed with status {response.status}: {error_text}")

                    result = {"status": "success", "result": await response.json()}
                    self._logger.debug(f" - task completed successfully: {node_id} - {result}")
                except Exception as e:
                    self._logger.error(f"Workflow execution error_pool: {str(e)}\n{traceback.format_exc()}")
                    result = {"status": "error_pool", "error_pool": str(e)}
                return result

    def run(self, node_id: str, node_info: Dict) -> Dict:
        node_type = node_info['type']
        if node_type == 'end':
            result = {"status": "success", "result": "DONE"}
        else:
            result = asyncio.run(self._call_api(node_id, node_info))
        return {node_id: result}