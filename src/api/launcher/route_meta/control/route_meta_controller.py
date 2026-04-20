#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.launcher.route_meta.access.route_meta_access_handler import RouteMetaAccessHandler


class RouteMetaController:
    def __init__(self, logger):
        self._logger = logger
        self._meta_access = RouteMetaAccessHandler(self._logger).get_access()

    def set_route_meta_ctl(self, prefix, module_name, class_name):
        self._meta_access.set_route_meta_access(prefix, module_name, class_name)

    def get_reoute_meta_ctl(self):
        route_meta = self._meta_access.get_route_meta_access()
        return route_meta
