#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ailand.dao.aidao import Service
from ..control.launcher_ctl import LauncherController
from fastapi.routing import APIRoute
import traceback
import sys


class DynamicRouterService(Service):
    def __init__(self, app, logger, db_conn):
        super().__init__(logger, db_conn)
        self._app = app
        self._logger = logger
        self._indexCount = 0
        self._db_conn = db_conn

        self._api_services = {}
        self._launcher_ctl = LauncherController(logger, db_conn)

    def _gen_api_route_path(self, prefix, path):
        path_list = prefix.split("/") + path.split("/")
        api_route_path = "/%s" % ("/".join([path for path in path_list if path]))
        return api_route_path

    def _is_dup_api_router(self, api_route_path):
        for route in self._app.routes:
            if isinstance(route, APIRoute):
                if route.path == api_route_path:
                    return True
                else:
                    continue
        return False

    def get_init_service_info(self):
        service_module_map_list = self._launcher_ctl.get_init_service_meta()
        # return service_module_map_list
        return []

    def get_api_service_info(self):
        return self._api_services

    def add_api_service(self, prefix, module_name, class_name, version=0):
        if f"{class_name}-{version}" in self._api_services.keys():
            return
        src_type = "SRC"
        # src_type = "ZIP"
        # api_router = None

        try:
            if src_type == 'ZIP':
                # helloworld params
                path = './api/user.zip'
                sys.path.insert(0, path)
                module_name = "user.account.user_account"
                class_name = 'UserAccountRouter'

                module = __import__(module_name, fromlist=[module_name])
                app_object = getattr(module, class_name)(self._logger, self._db_conn)
                api_router = app_object.get_router()

            elif src_type == 'SRC':
                self._logger.debug(f" - add api service: {module_name} - {class_name}")
                if 'api' != module_name.split('.')[0]:
                    module_name = f'api.{module_name}'
                module = __import__(module_name, fromlist=[module_name])
                app_object = getattr(module, class_name)(self._logger, self._db_conn)
                api_router = app_object.get_router()
            else:
                raise Exception("Module not defined")

            for route in api_router.routes:
                api_route_path = self._gen_api_route_path(prefix, route.path)
                if self._is_dup_api_router(api_route_path):
                    self.del_app_router(prefix, route.path)
                else:
                    self._set_api_services(prefix, module_name, class_name, route.path, version)

            self._app.include_router(api_router, prefix=prefix)
        except Exception as e:
            self._logger.error(traceback.format_exc())
            self._logger.error(e)

    def _set_api_services(self, prefix, module_name, class_name, route_path, version=0):
        service_key = f"{class_name}-{version}"
        if service_key in self._api_services.keys():
            api_service = self._api_services.get(service_key)
            if route_path not in api_service['route_paths']:
                api_service['route_paths'].append(route_path)
        else:
            self._api_services[service_key] = {
                'version': 0,
                'prefix': prefix,
                'module_name': module_name,
                'class_name': service_key,
                'route_paths': [route_path]
            }

    def del_app_router(self, prefix, route_path):
        del_index = []
        api_route_path = self._gen_api_route_path(prefix, route_path)
        for index, route in enumerate(self._app.router.routes):
            if isinstance(route, APIRoute):
                if route.path == api_route_path:
                    del_index.append(index)
        del_index.backward()
        for index in del_index:
            self._app.router.routes.pop(index)
