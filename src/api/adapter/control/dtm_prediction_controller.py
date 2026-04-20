#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.conf_adapter import getDownloadPath, getRemoteEngineUrl
from datetime import datetime, timezone, timedelta
from urllib.parse import quote, unquote
from api.adapter.access.dtm_prediction_access import DtmPredictionAccess
import base64
import json
import os


class DtmPredictionController:
    def __init__(self, logger, remote_adapter_service):
        self._logger = logger
        self._remote_adapter_service = remote_adapter_service
        self._prediction_access = DtmPredictionAccess(logger)
        self._upload_path = getDownloadPath()

    def cvt_to_json(self, data):
        try:
            clean_data = data.strip().rstrip(",").replace(",}", "}").replace(",]", "]")
            parsed_data = json.loads(clean_data)
            return parsed_data
        except json.JSONDecodeError as e:
            if not isinstance(data, dict):
                self._logger.warn(f"data")
            self._logger.warn(f"Invalid JSON in data field: {str(e)}")
            return data

    async def download_files_ctl(self, files):
        def curr_dt():
            tz_utc_minus_9 = timezone(timedelta(hours=-9))
            now = datetime.now(tz=tz_utc_minus_9)
            date_str = now.strftime("%Y%m%d")
            return date_str

        try:
            if len(files) < 1:
                raise FileNotFoundError("File to upload does not exist")
        except Exception as e:
            raise e

        upload_dir = os.path.join(self._upload_path, curr_dt())
        if not os.path.isdir(upload_dir):
            try:
                os.makedirs(upload_dir)
            except OSError as e:
                self._logger.error('fail to make directory')
                raise Exception('fail to make directory')

        path_list = []
        for file in files:
            file_nm = file.filename
            file_path = os.path.join(upload_dir, file_nm)

            content = await file.read()
            with open(file_path, 'wb') as wf:
                wf.write(content)
            path_list.append(file_path)
        return path_list

    def extract_request_info_ctl(self, job_id, headers, json_callback_data_body, file_path_list):
        if isinstance(headers, dict):
            x_sampl_callback = headers.get("x_sampl_callback")
            x_sampl_err_callback = headers.get("x_sampl_err_callback")
            member_id = headers.get("x_sampl_member_id")
            x_sampl_user_data = headers.get("x_sampl_user_data")
        else:
            x_sampl_callback = headers.x_sampl_callback
            x_sampl_err_callback = headers.x_sampl_err_callback
            member_id = headers.x_sampl_member_id
            x_sampl_user_data = headers.x_sampl_user_data

        tags = json_callback_data_body.get('tags', {})
        data_info = json_callback_data_body.get('data', {})

        call_back_url = unquote(x_sampl_callback)
        call_back_error_url = unquote(x_sampl_err_callback)

        self._logger.debug(f" - [{job_id}] call_back_url       : {call_back_url}")
        self._logger.debug(f" - [{job_id}] call_back_error_url : {call_back_error_url}")
        self._logger.debug(f" - [{job_id}] x_sampl_user_data   : {x_sampl_user_data}")
        self._logger.debug(f" - [{job_id}] tar_path_list       : {file_path_list}")
        self._logger.debug(f" - [{job_id}] data_info           : {data_info}")
        self._logger.debug(f" - [{job_id}] tags                : {tags}")

        header_info = {
            "Content-Type": "application/json",
            "secret_key": "",
            "job_id": f"{job_id}",
            "user_id": f"{member_id}",
            "file_path_list": json.dumps(file_path_list),
            "request-id": str(job_id),
            "session-id": str(job_id),
            "call_back_error_url": call_back_error_url,
            "call_back_url": call_back_url,
            "call_back_data_body": base64.b64encode(json.dumps(json_callback_data_body).encode()).decode(),
            "x_sampl_job_id": job_id,
            "x_sampl_callback": x_sampl_callback,
            "x_sampl_err_callback": x_sampl_err_callback,
            "x_sampl_member_id": member_id,
            "x_sampl_user_data": x_sampl_user_data
        }
        return header_info

    async def run_prediction_ctl(self, job_id, engine_header, file_path_list):
        self._logger.info(f"[{job_id}] Call prediction on engine")
        engine_params = {"tar_path": file_path_list}
        status_code = -1
        result_data = []
        result = {}

        try:
            engine_url = getRemoteEngineUrl()
            route_path = "/api/v1/workflow/inference"
            call_method = "POST"
            self._remote_adapter_service.set_job_state(job_id, state='RUNNING')
            result = await self._prediction_access.run_prediction_access(engine_url, route_path, call_method, engine_header, engine_params)

            self._logger.debug(f"[{job_id}] Job completed, result: {result}")
            result_message = result.get('result', {})
            if isinstance(result_message, dict):
                result_state = result_message.get('status')
                if result_state in ['success']:
                    result_file_path = result_message.get('result')
                    status_code = 0
                    status_text = result_state
                    result_data = self._prediction_access.read_result_file(result_file_path)
                else:
                    error_message = result_message.get('error')
                    status_code = -1
                    status_text = error_message
                    self._remote_adapter_service.set_job_state(job_id, state='ERROR', error_msg=error_message)
            else:
                status_text = 'ValidError: result format is not valid'
        except FileNotFoundError as e:
            self._logger.warn(f"[{job_id}]: file not found error, result: {result}")
            status_code = -1
            status_text = f"{type(e).__name__}: {e}"
        except Exception as e:
            self._logger.error(f"# Step 2: {e}")
            self._remote_adapter_service.set_job_state(job_id, state='ERROR', error_msg=str(e))
            status_code = -1
            status_text = f"{type(e).__name__}: {e}"

        result_pack = {
            'status_code': status_code,
            'status_text': status_text,
            'result_data': result_data
        }
        return result_pack

    async def run_callback_result_ctl(self, job_id, callback_header, callback_data_info, result_pack):
        self._logger.info(f"[{job_id}] Send result result data")
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
                self._logger.info(f"[{job_id}] This job does not perform a callback upon user request. - CALLBACKABLE: {callbackable}")
                self._logger.debug(f"[{job_id}] callback prediction result")
                self._logger.debug(f"[{job_id}] status_code: {status_code}, status_message: {status_text}")
                self._remote_adapter_service.set_job_state(job_id, state='COMPLETED')
            else:
                self._logger.info(f"[{job_id}] callback prediction result")
                self._logger.info(f"[{job_id}] status_code: {status_code}, status_message: {status_text}")
                result = await self._prediction_access.run_result_callback_access(url=callback_url, headers=headers, body=body)
                self._logger.info(f"[{job_id} callback success: {result}")
                self._remote_adapter_service.set_job_state(job_id, state='COMPLETED')
        except Exception as e:
            self._logger.error(e)
            self._remote_adapter_service.set_job_state(job_id, state='ERROR', error_msg=f"{type(e).__name__}: {e}")

