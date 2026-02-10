#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ailand.dao.aidao import Controller

from api.launcher.access.launcher_access import LauncherAccess


class LauncherController(Controller):
    def __init__(self, logger, db_conn):
        super().__init__(logger, db_conn)
        self._launcher_access = LauncherAccess(logger, db_conn)

    def get_init_service_meta(self):
        init_service_meta = self._launcher_access.get_init_service_data()
        return init_service_meta

    def get_service_meta(self, svc_pkg_id: str | None):
        service_meta = self._launcher_access.get_service_data(svc_pkg_id)
        return service_meta

    def add_svc_func_info(self, svc_pkg_id, api_route_path, route_path, method, func_modul_nm, perm_id):
        add_service_url = self._launcher_access.add_svc_func_info(svc_pkg_id, api_route_path, route_path, method, func_modul_nm, perm_id)
        return add_service_url

    def delete_service_routers(self, svc_pkg_id):
        delete_service_routers = self._launcher_access.delete_service_routers(svc_pkg_id)
        return delete_service_routers

    def get_service_routers(self, svc_pkg_id):
        service_routers = self._launcher_access.get_service_routers(svc_pkg_id)
        return service_routers

    def add_perm_info(self, perm_id, perm_nm, perm_desc, perm_pkg_nm):
        add_service_url = self._launcher_access.add_perm_info(perm_id, perm_nm, perm_desc, perm_pkg_nm)
        return add_service_url

    def add_perm_func_map(self, api_route_path, path, method, name, perm_id):
        add_perm_func_map = self._launcher_access.add_perm_func_map(api_route_path, path, method, name, perm_id)
        return add_perm_func_map

    def get_perm_id_from_perm_func_map(self, api_route_path, method):
        perm_id = self._launcher_access.get_perm_id_from_perm_func_map(api_route_path, method)
        return perm_id
