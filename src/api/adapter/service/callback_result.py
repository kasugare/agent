#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict
from urllib.parse import quote, unquote
import requests
import base64


class CallbackApiRequester:
    def __init__(self, logger):
        self._logger = logger
        self._timeout = 3600

    def _encode_base64_header_value(self, headers: dict, key: str) -> dict:
        if key in headers:
            header_value = headers.get(key)
            try:
                encoded_value = base64.b64encode(header_value.encode()).decode()
                headers[key] = encoded_value
            except Exception as e:
                self._logger.warn(f"header {key} is not encoded: {header_value}")
        return headers

    def _decode_base64_header_value(self, headers: dict, key: str) -> dict:
        header_value = headers.get(key)
        try:
            decoded_value = base64.b64decode(header_value).decode()
            headers[key] = decoded_value
        except Exception as e:
            self._logger.warn(f"header {key} is not decoded: {header_value}")
        return headers

    def _call_api_sync(self, url: str, base_url: str=None, route_path: str=None, method: str='get', headers: Dict = None, json_data: Dict = None, params: Dict = None):
        if not url:
            url = f"{base_url}{route_path}"
        try:
            # timeout=None --> unlimit, def: unlimit
            response = requests.request(
                method=method.upper(),
                url=url,
                json=json_data,
                headers=headers,
                timeout=self._timeout
            )
            if response.status_code >= 400:
                self._logger.error(f"API error: {response.text}")
                raise Exception(f"API error: {response.status_code}")

            return response.json()

        except requests.RequestException as e:
            self._logger.error(f"Request error: {str(e)}")
            raise

    def call_back_result(self, callback_header, callback_data_info, result_pack):
        job_id = callback_header.x_sampl_job_id
        call_back_url = unquote(callback_header.x_sampl_callback)
        call_back_error_url = unquote(callback_header.x_sampl_err_callback)
        user_callback_data = callback_header.x_sampl_user_data
        callbackable = callback_header.x_callbackable

        tags = callback_data_info.get('tags', {})
        data_info = callback_data_info.get('data', {})
        status_code = result_pack.get('status_code')
        status_text = result_pack.get('status_text')
        result_data = result_pack.get('result_data')

        if status_code == 0:
            callback_url = call_back_url
        else:
            callback_url = call_back_error_url

        if result_data:
            result_data = [result_data]

        headers = {
            'X-SAMPL-USER-DATA': user_callback_data,  # 온것 그대로
            'Content-Type': 'application/json; charset=UTF-8'
        }
        headers = self._encode_base64_header_value(headers, 'X-SAMPL-USER-DATA')
        body = {
            "status": status_code,  # success: 0, fail: -1
            "statusText": status_text,  # success: 'success', fail: 'error_msg'
            "data": {
                "project": "ocr",
                "blueprint": "detection",
                "tags": tags,
                "result": {
                    "uuid": "abc",
                    "image": result_data  # success: read json_result, fail: [],
                },
                "data": data_info
            }
        }

        try:
            if not callbackable:
                self._logger.warn(f"[{job_id}] This job does not perform a callback upon user request. - CALLBACKABLE: {callbackable}")
                self._logger.debug(f"[{job_id}] callback prediction result")
                self._logger.debug(f"[{job_id}] status_code: {status_code}, status_message: {status_text}")
            else:
                self._logger.info(f"[{job_id}] callback prediction result")
                self._logger.info(f"[{job_id}] status_code: {status_code}, status_message: {status_text}")
                self._call_api_sync(url=callback_url, method='post', headers=headers, json_data=body)
        except Exception as e:
            self._logger.error(e)
