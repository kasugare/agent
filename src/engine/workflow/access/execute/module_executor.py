#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Any, Dict, List, Optional, Union
from engine.workflow.common.util_dynamic_loader import DynamicLoader
import traceback
import inspect


class ModuleExecutor(DynamicLoader):
    def __init__(self, logger, module_path, class_name, function_name):
        super().__init__(logger)
        self._logger = logger
        self._module_path = module_path
        self._class_name = class_name
        self._function_name = function_name
        self._env_params = {}
        self._func_params = {}

    def set_env(self, env_params):
        self._env_params = env_params

    def set_params(self, func_params):
        self._func_params = func_params

    def get_env(self):
        return self._env_params

    def get_params(self):
        return self._func_params

    def run(self, *args, **kwargs) -> Any:
        try:
            if self._class_name:
                instance = self.create_instance(self._module_path, self._class_name, self._env_params)
                result = self.call_class_method(instance, self._function_name, *args, **kwargs)
            else:
                result = self.call_module_function(self._module_path, self._function_name, *args, **kwargs)
        except Exception as e:
            self._logger.error(e)
            raise RuntimeError
        return result