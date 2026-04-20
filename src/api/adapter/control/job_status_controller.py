#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.adapter.access.job_status_access import JobStatusAccess


class JobStatusController:
    def __init__(self, logger):
        self._logger = logger
        self._job_status_access = JobStatusAccess(logger)

    async def get_working_state_ctl(self):
        def is_available(status_map):
            status = status_map.get('status', {})
            available_nodes = status.get('available', 0)
            if available_nodes > 0:
                return True
            return False
        try:
            working_state = await self._job_status_access.get_working_state_access()
            status_info = working_state.get('status_map', {})
            if all(is_available(status_map) for node_id, status_map in status_info.items()):
                is_working = False
            else:
                is_working = True
        except Exception as e:
            self._logger.error(e)
            working_state = {
                "state": -1,
                "message": "InternalServerError"
            }
            is_working = False

        status = working_state.get('state')
        status_message = working_state.get('message')

        if not isinstance(status, int):
            status = -1
        if not isinstance(status_message, str):
            status_message = str(status_message)

        result_format = {
            "data": {
                "isworking": is_working,
                "async_queue_count": 0,
                "job_list": []
            },
            "status": status,
            "statusText": status_message
        }
        self._logger.debug(result_format)
        return result_format

    async def get_job_status_detail_info_ctl(self, job_id, job_status):
        job_status_dtl_info = await self._job_status_access.get_job_status_detail_access(job_id)

        if not job_status_dtl_info:
            completion_yn = 'N'
            reg_datetime = "0"
            start_datetime = "0"
            end_datetime = "0"
            engine_status = 'RUNNING'
            call_back_url = None
            call_back_error_url = None
            error_yn = 'N'
        else:
            processing_time = job_status_dtl_info.get('processing_time')
            reg_datetime = processing_time.get('assigned_dt', "0")
            start_datetime = processing_time.get('start_dt', "0")
            end_datetime = processing_time.get('end_dt', "0")
            engine_status = job_status_dtl_info.get('status')
            user_params = job_status_dtl_info.get('user_params', {})

            if user_params:
                call_back_url = user_params.get('call_back_url', None)
                call_back_error_url = user_params.get('call_back_error_url', None)
            else:
                call_back_url = None
                call_back_error_url = None

            if engine_status == 'COMPLETED':
                if job_status.get('state') == 'COMPLETED':
                    completion_yn = 'Y'
                    error_yn = "N"
                elif job_status.get('state') == 'ERROR':
                    completion_yn = 'Y'
                    error_yn = "Y"
                else:
                    completion_yn = 'N'
                    error_yn = "N"
            elif engine_status == 'FAILED':
                completion_yn = 'Y'
                error_yn = "Y"
            else:
                completion_yn = 'N'
                error_yn = 'N'

        result_format = {
            "data": {
                "cnt": 0,
                "data": [{
                    "call_back_error_url": call_back_error_url,
                    "call_back_url": call_back_url,
                    "completion_yn": completion_yn,
                    "conveyor": "ocr_online",
                    "data": {},
                    "end_datetime": end_datetime,
                    "error_yn": error_yn,
                    "job_id": job_id,
                    "member_id": "",
                    "message": "Success",
                    "notified": "",
                    "pid": 0,
                    "pid_created_time": 0,
                    "reg_datetime": reg_datetime,
                    "start_datetime": start_datetime,
                    "status": engine_status,
                    "thread_id": 0,
                    "uid": ""
                }]
            },
            "status": 0,
            "statusText": "success"
        }
        return result_format
