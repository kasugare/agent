#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.launcher.route_meta.control.route_meta_controller import RouteMetaController


class RouteMetaService:
    def __init__(self, logger):
        self._logger = logger
        self._meta_controller = RouteMetaController(logger)

    def set_route_meta(self):
        pass

    def get_route_meta(self):
        route_meta = self._meta_controller.get_reoute_meta_ctl()
        return route_meta



