#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List, Any, Optional
import traceback
import asyncio
import aiohttp
import json


class ApiExecutor:
    def __init__(self, logger, url, method, header={}):
        self._logger = logger
        self._url = url
        self._method = method.upper()  # GET, POST, PUT, DELETE, PATCH
        self._header = header
        self._env_params = {}
        self._asset_params = {}
        self._params = {}

    def set_url(self, url):
        self._url = url

    def get_url(self):
        return self._url

    def set_env(self, env_params):
        self._env_params = env_params

    def set_asset(self, asset_params):
        self._asset_params = asset_params

    def set_params(self, params):
        self._params = params

    def get_params(self):
        if not self._params:
            return {}
        return self._params

    def _build_headers(self) -> Dict[str, str]:
        headers = {}
        if self._header:
            headers.update(self._header)

        if self._env_params:
            for key, value in self._env_params.items():
                if key == 'api_key':
                    headers['X-API-Key'] = value
                elif key == 'auth_token':
                    headers['Authorization'] = f"Bearer {value}"
                elif key == 'content_type':
                    headers['Content-Type'] = value
                elif 'custom_headers' in self._env_params:
                    headers.update(value)
                else:
                    headers[key] = value
            if 'Content-Type' not in self._env_params:
                headers['Content-Type'] = 'application/json'

        if self._asset_params:
            if 'asset_id' in self._asset_params:
                headers['X-Asset-ID'] = str(self._asset_params['asset_id'])
            elif 'asset_token' in self._asset_params:
                headers['X-Asset-Token'] = self._asset_params['asset_token']
            else:
                for key, value in self._asset_params.items():
                    headers[key] = value

        self._logger.debug(f"Built headers: {headers}")
        return headers

    async def _call_api(self) -> Dict:
        headers = self._build_headers()
        params = self.get_params()

        async with aiohttp.ClientSession() as session:
            try:
                if self._method == 'GET':
                    # GET 요청: query parameter로 전달
                    async with session.get(
                            self.get_url(),
                            headers=headers,
                            params=params
                    ) as response:
                        return await self._handle_response(response)

                elif self._method == 'POST':
                    # POST 요청: body에 JSON으로 전달
                    async with session.post(
                            self.get_url(),
                            headers=headers,
                            json=params
                    ) as response:
                        return await self._handle_response(response)

                elif self._method == 'PUT':
                    # PUT 요청: body에 JSON으로 전달
                    async with session.put(
                            self.get_url(),
                            headers=headers,
                            json=params
                    ) as response:
                        return await self._handle_response(response)

                elif self._method == 'PATCH':
                    # PATCH 요청: body에 JSON으로 전달
                    async with session.patch(
                            self.get_url(),
                            headers=headers,
                            json=params
                    ) as response:
                        return await self._handle_response(response)

                elif self._method == 'DELETE':
                    # DELETE 요청: query parameter 또는 body로 전달
                    async with session.delete(
                            self.get_url(),
                            headers=headers,
                            json=params if params else None
                    ) as response:
                        return await self._handle_response(response)

                else:
                    raise ValueError(f"Unsupported HTTP method: {self._method}")

            except Exception as e:
                self._logger.error(
                    f"API call error: {str(e)}\n{traceback.format_exc()}"
                )
                raise

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict:
        """
        API 응답 처리
        """
        try:
            if response.status >= 400:
                error_json = await response.json()
                self._logger.error(
                    f"Error details (JSON): {json.dumps(error_json, indent=2)}"
                )
                raise Exception(
                    f"API call failed with status {response.status}: {error_json}"
                )

            result = {
                "status": "success",
                "result": await response.json()
            }
            self._logger.debug(f"Task completed successfully: {result}")
            return result

        except aiohttp.ContentTypeError:
            # JSON이 아닌 응답인 경우
            text_result = await response.text()
            if response.status >= 400:
                self._logger.error(f"Error details (text): {text_result}")
                raise Exception(
                    f"API call failed with status {response.status}: {text_result}"
                )
            result = {
                "status": "success",
                "result": text_result
            }
            return result

        except Exception as e:
            self._logger.error(
                f"Workflow execution error: {str(e)}\n{traceback.format_exc()}"
            )
            result = {
                "status": "error",
                "error": str(e)
            }
            raise

    def run(self, **params):
        """
        동기 방식으로 API 실행
        """
        self._logger.info(f"[Executor] Call API: {params}")
        self.set_params(params)
        result = asyncio.run(self._call_api())
        result_map = result.get('result')
        return result_map