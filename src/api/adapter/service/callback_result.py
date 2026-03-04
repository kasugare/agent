#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict
import requests


class CallbackApiRequester:
    def __init__(self, logger):
        self._logger = logger

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

    def call_back_result(self, callback_header, callback_data_info, result_pack):
        job_id = callback_header.x_sampl_job_id
        call_back_url = callback_header.x_sampl_callback
        call_back_error_url = callback_header.x_sampl_err_callback
        user_callback_data = callback_header.x_sampl_user_data
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
            'Content-Type': 'application/json'
        }
        body = {
            "status": status_code,  # 성공: 0, 실패: -1
            "statusText": status_text,  # 성공: success, 실패: error_msg
            "data": {
                "project": "ocr",
                "blueprint": "detection",
                "tags": tags,
                "result": {
                    "uuid": "abc",
                    "image": result_data  # 실패시: [], 성공: 아래 포멧
                },
                "data": data_info
            }
        }

        try:
            self._logger.info(f"[{job_id}] callback prediction result")
            self._logger.info(f"[{job_id}] status_code: {status_code}, status_message: {status_text}")
            self._call_api_sync(url=callback_url, method='post', headers=headers, json_data=body)
        except Exception as e:
            self._logger.error(e)