# -*- coding: utf-8 -*-
#!/usr/bin/env python


from typing import Any, Dict, List, Optional, Union
import importlib
import traceback
import importlib
import inspect
import sys
import os


class DynamicLoader:
    # _instance = None
    #
    # def __new__(cls, *args, **kwargs):
    #     if cls._instance is None:
    #         cls._instance = super().__new__(cls)
    #     return cls._instance

    def __init__(self, logger):
        self._logger = logger
        self._loaded_modules = {}
        self._instance_pool = {}
        self._add_path("/Users/hanati/workspace/agent/src")

    def _load_module(self, module_path: str, reload: bool = False) -> Any:
        """ module_path: "app.test.test_class" """
        try:
            if module_path in self._loaded_modules and not reload:
                return self._loaded_modules[module_path]
            module = importlib.import_module(module_path)
            if reload:
                module = importlib.reload(module)
            self._loaded_modules[module_path] = module
            return module

        except ImportError as e:
            self._logger.error(f"failed load a module {module_path} - {e}")
            raise
        except Exception as e:
            self._logger.error(f"not expected error: {e}")
            raise

    def _gen_instance_key(self, module_path, class_name):
        instance_key = f"{module_path}.{class_name}"
        return instance_key

    def _add_path(self, path: str) -> None:
        abs_path = os.path.abspath(path)
        if abs_path not in sys.path:
            sys.path.insert(0, abs_path)

    def create_instance(self, module_path: str, class_name: str, env_params: Dict[str, Any] = None, instance_key: str = None) -> Any:
        try:
            if env_params is None:
                env_params = {"logger": self._logger}
            else:
                env_params['logger'] = self._logger

            module = self._load_module(module_path)
            if not hasattr(module, class_name):
                raise AttributeError(f"'{class_name}'(class) is not exist in '{module_path}'.")
            target_class = getattr(module, class_name)

            if not inspect.isclass(target_class):
                raise TypeError(f"'{class_name}' is not a class")

            # create class instance
            if isinstance(env_params, dict):
                instance = target_class(**env_params)
            else:
                instance = target_class(env_params)

            # save instance in cache
            if instance_key is None:
                instance_key = self._gen_instance_key(module_path, class_name)

            self._instance_pool[instance_key] = instance
            return instance

        except Exception as e:
            self._logger.error(f"fail to carete class instance: {e}")
            traceback.print_exc()
            raise

    def get_class_instance(self, module_path, class_name):
        instance_key = self._gen_instance_key(module_path, class_name)
        instance = self._instance_pool.get(instance_key)
        return instance

    def get_available_methods(self, instance: Any) -> List[str]:
        available_methods = [method for method in dir(instance)
                if not method.startswith('_') and callable(getattr(instance, method))]
        return available_methods

    def get_module_functions(self, module: Any) -> List[str]:
        module_functions = [name for name in dir(module)
                if not name.startswith('_')
                and callable(getattr(module, name))
                and not inspect.isclass(getattr(module, name))]
        return module_functions

    def _extract_function_params(self, target_signature):
        function_params = {
            param.name: {
                "annotation": param.annotation if param.annotation != param.empty else None,
                "default": param.default if param.default != param.empty else None
            }
            for param in target_signature.parameters.values()
        }
        return function_params

    def get_function_info(self, instance: Any, function_name: str) -> Dict[str, Any]:
        function_info = {}
        try:
            if not hasattr(instance, function_name):
                self._logger.warn(f"'{function_name}' is not exist.")
                return function_info

            target_function = getattr(instance, function_name)
            if not callable(target_function):
                self._logger.warn(f"'{function_name}' is not callable functions")
                return function_info

            function_signature = inspect.signature(target_function)
            function_params = self._extract_function_params(function_signature)
            function_info = {
                "name": function_name,
                "module": None,
                "signature": str(function_signature),
                "parameters": function_params,
                "doc": target_function.__doc__,
                "type": "function"
            }
        except Exception as e:
            self._logger.error(e)
        return function_info

    def get_module_function_info(self, module_path: str, function_name: str) -> Dict[str, Any]:
        module_function_info = {}
        try:
            module = self._load_module(module_path)
            if not hasattr(module, function_name):
                self._logger.error(f"'{function_name}' is not exist in '{module_path}'.")
                return {}

            target_function = getattr(module, function_name)
            if not callable(target_function):
                self._logger.error(f"'{function_name}' is not callable.")
                return {}

            if inspect.isclass(target_function):
                self._logger.error(f"'{function_name}' is a class(module). not callable function")
                return {}

            module_function_signature = inspect.signature(target_function)
            function_params = self._extract_function_params(module_function_signature)

            module_function_info = {
                "name": function_name,
                "module": module_path,
                "signature": str(module_function_signature),
                "parameters": function_params,
                "doc": target_function.__doc__,
                "type": "module_function"
            }
        except Exception as e:
            self._logger.error(f"failed search parameter's info: {e}")
        return module_function_info
