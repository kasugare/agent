#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.adapter.control.job_status_controller import JobStatusController


class JobStatusService:
    def __init__(self, logger, remote_adapter_service):
        self._logger = logger
        self._remote_adapter_service = remote_adapter_service
        self._job_status_controller = JobStatusController(logger)

    async def get_is_working(self):
        working_statue_result = await self._job_status_controller.get_working_state_ctl()
        return working_statue_result

    async def get_job_list(self, job_id):
        job_status = self._remote_adapter_service.get_job_status(job_id)
        job_status_result = await self._job_status_controller.get_job_status_detail_info_ctl(job_id, job_status)
        return job_status_result
