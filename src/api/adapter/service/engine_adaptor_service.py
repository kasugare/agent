#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.conf_adapter import getDownloadPath
import os


class EngineAdaptorService:
    def __init__(self, logger):
        self._logger = logger
        self._pjt_id = 'pjt_id'
        self._wf_id = 'wf_id'
        self._upload_path = getDownloadPath()

    async def upload_files(self, files):
        try:
            if len(files) < 1:
                raise FileNotFoundError("File to upload does not exist")
        except Exception as e:
            raise e
        upload_dir = os.path.join(self._upload_path, self._pjt_id , self._wf_id)
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