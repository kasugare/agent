# -*- coding: utf-8 -*-
#!/usr/bin/env python

from common.conf_system import getRouteAccessType
from api.launcher.route_meta.access.route_meta_file_access import RouteMetaFileAccess


class RouteMetaAccessHandler:
    def __init__(self, logger):
        self._logger = logger
        self._access_type = getRouteAccessType()

    def get_access(self):
        meta_access = None
        if self._access_type.lower() == 'file':
            meta_access = RouteMetaFileAccess(self._logger)
        else:
            self._logger.error(f"Not defined type error: {self._access_type}")
            raise
        return meta_access