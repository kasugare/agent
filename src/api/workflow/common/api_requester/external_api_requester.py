#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict
import requests


class ExternalApiRequester:
    def __init__(self, logger):
        self._logger = logger

    def call_api_sync(self, base_url: str, method: str, route_path: str, headers: Dict = None, json_data: Dict = None, params: Dict = None):
        """동기 API 호출 - requests 사용"""
        url = f"{base_url}{route_path}"

        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                json=json_data,
                params=params,
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