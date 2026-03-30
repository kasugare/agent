#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.conf_system import getLockDir, getRouteDirPath, getRouteFileName
from api.launcher.route_meta.access.route_meta_access_interface import RouteMetaAccessInterface
import json
import os


class RouteMetaRedisAccess(RouteMetaAccessInterface):
    def __init__(self, logger):
        self._logger = logger
        self._route_dir_path = getRouteDirPath()
        self._route_file_name = getRouteFileName()
        self._route_file_path = os.path.join(self._route_dir_path, self._route_file_name)

    def set_route_meta_access(self):
        pass

    def get_route_meta_access(self):
        route_info = {}
        with open(self._route_file_path, 'r') as fd:
            try:
                route_info = json.load(fd)
            except json.JSONDecodeError:
                self._logger.error("Invalid routes file format")
            except Exception as e:
                pass
        return route_info


