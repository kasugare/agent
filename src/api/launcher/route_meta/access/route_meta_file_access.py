#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.conf_system import getLockDir, getRouteDirPath, getRouteFileName
from api.launcher.utility.file_lock import FileLock
from api.launcher.route_meta.access.route_meta_access_interface import RouteMetaAccessInterface
import json
import os


class RouteMetaFileAccess(RouteMetaAccessInterface):
    def __init__(self, logger):
        self._logger = logger
        self._route_dir_path = getRouteDirPath()
        self._route_file_name = getRouteFileName()
        self._route_file_path = os.path.join(self._route_dir_path, self._route_file_name)

    def set_route_meta_access(self, prefix, module_name, class_name):
        try:
            if os.path.exists(self._route_file_path):
                with FileLock(f"{getLockDir()}/routes.lock"):
                    with open(self._route_file_path, 'r') as f:
                        try:
                            service_info = json.load(f)
                        except json.JSONDecodeError:
                            service_info = {}

                    service_info[class_name] = {
                        'prefix': prefix,
                        'module_name': module_name,
                        'class_name': class_name
                    }

                    with open(self._route_file_path, 'w') as fd:
                        json.dump(service_info, fd, indent=2)
        except Exception as e:
            self._logger.error(e)

    def get_route_meta_access(self):
        route_info = {}
        with FileLock(f"{getLockDir()}/routes.lock"):
            with open(self._route_file_path, 'r') as fd:
                try:
                    route_info = json.load(fd)
                except json.JSONDecodeError:
                    self._logger.error("Invalid routes file format")
                except Exception as e:
                    pass
        return route_info

