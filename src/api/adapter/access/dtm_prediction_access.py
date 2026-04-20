#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.adapter.access.connector.exteranl_api_requester import ExternalApiRequester
import asyncio
import json


class DtmPredictionAccess(ExternalApiRequester):
    def __init__(self, logger):
        super().__init__(logger)
        self._logger = logger

    def read_result_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as fd:
                json_data = json.load(fd)
        except FileNotFoundError:
            self._logger.warn("File not found error")
            raise FileNotFoundError
        except json.JSONDecodeError:
            self._logger.warn("json decoding error")
            raise json.JSONDecodeError
        except Exception as e:
            self._logger.error(e)
            raise Exception
        return json_data

    async def run_prediction_access(self, base_url, route_path, method, req_headers, json_data):
        result = await asyncio.create_task(
            self.call_external_api(
                base_url=base_url,
                path=route_path,
                method=method,
                headers=req_headers,
                json_data=json_data
            )
        )
        return result

    async def run_result_callback_access(self, url, headers, body):
        result = await self.call_api_sync(url=url, method='post', headers=headers, json_data=body)
        return result

