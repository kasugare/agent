#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.adapter.schema.engine_adaptor_header import get_file_headers, FileHeaderModel
from api.adapter.control.dtm_prediction_controller import DtmPredictionController
from fastapi import BackgroundTasks



class DtmPredictionService:
    def __init__(self, logger, remote_adapter_service):
        self._logger = logger
        self._remote_adapter_service = remote_adapter_service
        self._prediction_controller = DtmPredictionController(logger, remote_adapter_service)

    def _show_data(self, data_info):
        if isinstance(data_info, dict):
            for key, value in data_info.items():
                self._logger.debug(f'    L {key}: {value}')
        elif isinstance(data_info, list) or isinstance(data_info, set):
            self._logger.debug(f'    L {data_info}')
        else:
            self._logger.debug(f'    L {data_info}')

    async def _run_background_job(self, job_id, file_path_list, engine_header, callback_header, callback_data_info):
        result_pack = await self._prediction_controller.run_prediction_ctl(job_id, engine_header, file_path_list)
        await self._prediction_controller.run_callback_result_ctl(job_id, callback_header, callback_data_info, result_pack)

    async def run_dtm_prediction(self, request, req_headers, callback_data_body, upload_files, bg: BackgroundTasks=None):
        try:
            job_id = req_headers.x_sampl_job_id
            self._logger.info(f"# {[job_id]} Step 1: download data")
            file_path_list = await self._prediction_controller.download_files_ctl(upload_files)
            self._logger.debug(f"  L file path: {file_path_list}")

            self._logger.info(f"# {[job_id]} Step 2: extract callback data info")
            json_callback_data_body = self._prediction_controller.cvt_to_json(callback_data_body)
            self._show_data(json_callback_data_body)

            self._logger.info(f"# {[job_id]} Step 3: extract engine parameter info")
            engine_header = self._prediction_controller.extract_request_info_ctl(job_id, req_headers, json_callback_data_body, file_path_list)
            self._show_data(engine_header)

            self._logger.info(f"# {[job_id]} Step 4: reqeust prediction job to third_party(engine)")
            self._logger.warn(req_headers)
            bg.add_task(self._run_background_job, job_id, file_path_list, engine_header, req_headers, json_callback_data_body)
            response = {
                "data": {},
                "status": 0,
                "statusText": "success"
            }
        except Exception as e:
            self._logger.error(e)
            self._remote_adapter_service.set_job_state(job_id, state='ERROR', error_msg=str(e))
            response = {
                "data": {},
                "status": -1,
                "statusText": "failed"
            }
        return response

    async def rerun_dtm_prediction(self, job_id, callbackable, job_info, bg):
        try:
            import base64, json
            file_path_list = job_info.get('tar_path')
            self._logger.debug(f"  L file path: {file_path_list}")

            self._logger.info(f"# {[job_id]} Step 2: extract callback data info")
            callback_data_body = job_info.get('call_back_data_body')
            callback_data_body = base64.b64decode(callback_data_body).decode()
            json_callback_data_body = self._prediction_controller.cvt_to_json(callback_data_body)
            self._show_data(json_callback_data_body)

            self._logger.info(f"# {[job_id]} Step 3: generate request header")
            req_headers = FileHeaderModel
            req_headers.x_sampl_callback = job_info.get("x_sampl_callback")
            req_headers.x_sampl_err_callback = job_info.get("call_back_error_url")
            req_headers.x_sampl_member_id = job_info.get("x_sampl_member_id")
            req_headers.x_sampl_user_data = job_info.get("x_sampl_user_data")
            if callbackable.lower() == 'true':
                req_headers.x_callbackable = True
            else:
                req_headers.x_callbackable = False

            engine_header = self._prediction_controller.extract_request_info_ctl(job_id, req_headers, json_callback_data_body, file_path_list)
            self._show_data(engine_header)

            self._logger.info(f"# {[job_id]} Step 4: reqeust prediction job to third_party(engine)")
            bg.add_task(self._run_background_job, job_id, file_path_list, engine_header, req_headers, json_callback_data_body)
            response = {
                "data": {},
                "status": 0,
                "statusText": "success"
            }
        except Exception as e:
            self._logger.error(e)
            self._remote_adapter_service.set_job_state(job_id, state='ERROR', error_msg=str(e))
            response = {
                "data": {},
                "status": -1,
                "statusText": "failed"
            }
        return response

