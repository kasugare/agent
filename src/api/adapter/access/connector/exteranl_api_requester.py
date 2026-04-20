#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict
from fastapi import HTTPException
import requests
import asyncio
import httpx
import json


class ExternalApiRequester:
    def __init__(self, logger):
        self._logger = logger
        self._timeout = None

    def set_timeout(self, timeout):
        self._timeout = timeout
        # httpx:    timeout=None --> unlimit, def: 5s
        # requests: timeout=None --> unlimit, def: unlimit

    async def call_external_api(self, base_url: str, path: str, method: str, headers: Dict = None, json_data: Dict = None, params: Dict = None, timeout: int =None):
        if not base_url:
            raise HTTPException(
                status_code=500,
                detail=f"Internal API call failed: - check base_url: {base_url}"
            )
        if base_url[-1] == "/":
            url_path = f"{base_url[:-1]}{path}"
        else:
            url_path = f"{base_url}{path}"

        async with httpx.AsyncClient() as client:
            try:
                # timeout=None --> unlimit, def: 5s
                if method.upper() == "POST":
                    response = await client.post(url_path, json=json_data, headers=headers, timeout=timeout)
                elif method.upper() == "GET":
                    response = await client.get(url_path, params=params, headers=headers, timeout=timeout)
                elif method.upper() == "PUT":
                    response = await client.put(url_path, json=json_data, headers=headers, timeout=timeout)
                elif method.upper() == "DELETE":
                    response = await client.delete(url_path, headers=headers, timeout=timeout)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                if response.status_code >= 400:
                    error_detail = response.json() if response.headers.get('content-type') == 'application/json' else response.text
                    self._logger.error(f"Workflow Engine API error: {error_detail}")
                    self._logger.error(f"  L base_url: {base_url}")
                    self._logger.error(f"  L path: {path}")
                    self._logger.error(f"  L method: {method}")
                    self._logger.error(f"  L headers: {headers}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=error_detail
                    )
                return response.json()

            except httpx.RequestError as e:
                self._logger.error(f"Request error calling workflow API: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Internal API call failed: {str(e)}"
                )
            except Exception as e:
                raise

    async def call_api_sync(self, url: str, base_url: str=None, route_path: str=None, method: str='get', headers: Dict = None, json_data: Dict = None, params: Dict = None):
        if not url:
            url = f"{base_url}{route_path}"
        try:
            # timeout=None --> unlimit, def: unlimit
            response = requests.request(
                method=method.upper(),
                url=url,
                json=json_data,
                headers=headers,
                timeout=None
            )
            if response.status_code >= 400:
                self._logger.error(f"API error: {response.text}")
                raise Exception(f"API error: {response.status_code}")

            return response.json()

        except requests.RequestException as e:
            self._logger.error(f"Request error: {str(e)}")
            raise


