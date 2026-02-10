# -*- coding: utf-8 -*-
# !/usr/bin/env python
from ailand.dao.aidao import Access

from api.launcher.access.query_pool import *


class LauncherAccess(Access):
    def __init__(self, logger, db_conn):
        super().__init__(logger, db_conn)
        self._logger = logger

    def get_init_service_data(self):
        query_string = select_service_module_query(svc_pkg_id=None)
        data_list = self.execute_get(query_string)
        return data_list

    def get_service_data(self, svc_pkg_id: str | None):
        query_string = select_service_module_query(svc_pkg_id)
        data_list = self.execute_get(query_string)
        return data_list

    def add_svc_func_info(self, svc_pkg_id, api_route_path, route_path, method, func_modul_nm, perm_id):
        query_string = insert_svc_func_info_query(svc_pkg_id, api_route_path, route_path, method, func_modul_nm, perm_id)
        try:
            result = self.execute_set(query_string)
        except Exception as e:
            self._logger.error(f"query_string : {query_string}")
        return result

    def delete_service_routers(self, svc_pkg_id):
        query_string = delete_service_routers_query(svc_pkg_id)
        result = self.execute_set(query_string)
        return result

    def get_service_routers(self, svc_pkg_id):
        query_string = get_service_routers_query(svc_pkg_id)
        router_list = self.execute_get(query_string)
        return router_list

    def add_perm_info(self, perm_id, perm_nm, perm_desc, perm_pkg_nm):
        query_string = insert_perm_info_query(perm_id, perm_nm, perm_desc, perm_pkg_nm)
        result = self.execute_set(query_string)
        return result

    def add_perm_func_map(self, api_route_path, path, method, name, perm_id):
        query_string = add_perm_func_map_query(api_route_path, path, method, name, perm_id)
        result = self.execute_set(query_string)
        return result

    def get_perm_id_from_perm_func_map(self, api_route_path, method):
        query_string = get_perm_id_from_perm_func_map(api_route_path, method)
        result = self.execute_get_one(query_string)
        return result
