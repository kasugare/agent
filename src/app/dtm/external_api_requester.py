#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict
import requests
import json


class ExternalApiRequester:
    def __init__(self, logger, asset_info):
        self._logger = logger
        self._set_asset(asset_info)

    def _set_asset(self, asset_info):
        self._asset_info = asset_info

    def _call_api_sync(self, url: str, base_url: str=None, route_path: str=None, method: str='get', headers: Dict = None, json_data: Dict = None, params: Dict = None):
        if not url:
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

    def _read_file(self, file_path):
        json_data = {}
        try:
            with open(file_path, 'r', encoding='utf-8') as fd:
                json_data = json.load(fd)
        except FileNotFoundError:
            self._logger.warn("File not found error")
        except json.JSONDecodeError:
            self._logger.warn("json decoding error")
        return json_data

    def call_external_api(self, callback_url, callback_error_url, user_id, file_path_list, result_path):
        error_msg = ""
        try:
            result_json = self._read_file(result_path)
            url = callback_url
        except Exception as e:
            self._logger.warn(e)
            result_json = {
                "error": str(e)
            }
            error_msg = str(e)
            url = callback_error_url

        body = {
            "status": 0,
            "statusText": "success",
            "data": {
                "project": "ocr",
                "blueprint": "detection",
                "tags": {},
                "result": {
                    "uuid": "abc",
                    "image": [
                        {
                            "uuid": 1,
                            "name": file_path_list,
                            "success": "Y",
                            "page": 1,
                            "data": [],
                            "documentClassification": [],
                            "textExtraction": [],
                            "extData": {
                                "extract": []
                            },
                            "error": {
                                "code": 0,
                                "msg": f'{error_msg}'
                            }
                        }
                    ]
                },
                "data": {
                    "user_id": user_id,
                    "user_uid": 1,
                    "site_uid": 1,
                    "infer_uid": 1,
                    "batch_uid": "",
                    "uuid": ""
                }
            }
        }
        headers = {
            'X-SAMPL-USER-DATA': json.dumps(result_json),
            'Content-Type': 'application/json'
        }
        try:
            result = self._call_api_sync(url=url, method='post', json_data=body, headers=headers)
        except Exception as e:
            self._logger.error(e)
            raise
        return result