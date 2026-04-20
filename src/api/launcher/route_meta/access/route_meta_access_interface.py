#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod


class RouteMetaAccessInterface(ABC):
    @abstractmethod
    def set_route_meta_access(self, prefix, module_name, class_name) -> None:
        pass

    @abstractmethod
    def get_route_meta_access(self) -> dict:
        pass
