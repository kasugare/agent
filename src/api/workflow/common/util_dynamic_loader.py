# -*- coding: utf-8 -*-
#!/usr/bin/env python


from typing import Any, Dict, List, Optional, Union
from concurrent.futures import ThreadPoolExecutor
import importlib
import traceback
import importlib
import inspect
import asyncio
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

    def _process_arguments(self, args: tuple, kwargs: dict, signature: inspect.Signature) -> tuple:
        final_args = []
        final_kwargs = {}

        params = list(signature.parameters.values())
        param_names = [param.name for param in params if param.name != 'self']

        self._logger.debug(f"Target function parameters: {param_names}")

        # Case 1: args가 하나이고 그것이 dict인 경우 (가장 흔한 케이스)
        if len(args) == 1 and isinstance(args[0], dict) and not kwargs:
            self._logger.debug("Case 1: Single dict argument detected")
            arg_dict = args[0]

            # dict의 키가 함수 파라미터와 일치하는지 확인
            dict_keys = set(arg_dict.keys())
            param_set = set(param_names)

            if dict_keys.issubset(param_set) or dict_keys.intersection(param_set):
                # dict를 kwargs로 변환
                final_kwargs = arg_dict.copy()
                self._logger.debug("Converted dict to kwargs")
            else:
                # dict를 첫 번째 위치 인수로 처리
                final_args = [arg_dict]
                self._logger.debug("Kept dict as positional argument")

        # Case 2: kwargs만 있는 경우
        elif not args and kwargs:
            self._logger.debug("Case 2: Only kwargs provided")
            final_kwargs = kwargs.copy()

        # Case 3: args와 kwargs 모두 있는 경우
        elif args and kwargs:
            self._logger.debug("Case 3: Both args and kwargs provided")
            final_args = list(args)
            final_kwargs = kwargs.copy()

        # Case 4: args만 있고 dict가 아닌 경우
        elif args and not kwargs:
            self._logger.debug("Case 4: Only positional args provided")
            final_args = list(args)

        # Case 5: 아무것도 없는 경우
        else:
            self._logger.debug("Case 5: No arguments provided")
            pass

        return tuple(final_args), final_kwargs

    async def _call_async_method(self, method, *args, **kwargs):
        self._logger.debug(f"Calling async method: {method.__name__}")
        result = await method(*args, **kwargs)
        return result

    def _run_async_method_in_new_loop(self, async_method, *args, **kwargs) -> Any:
        return asyncio.run(self._call_async_method(async_method, *args, **kwargs))

    def _run_async_in_sync(self, async_method, *args, **kwargs) -> Any:
        def has_event_loop():
            has_running_event_loop = False
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                has_running_event_loop = True
            return has_running_event_loop

        self._logger.debug("Running async method in sync context")
        try:
            asyncio.get_running_loop()
            self._logger.debug(f"Event loop is already running, using thread executor")
            with ThreadPoolExecutor() as executor:
                future = executor.submit(self._run_async_method_in_new_loop, async_method, *args, **kwargs)
                result = future.result()
        except RuntimeError:
            result = self._run_async_method_in_new_loop(async_method, *args, **kwargs)
        return result

    def call_class_method(self, instance, function_name, *args, **kwargs) -> Any:
        def is_async_function(func) -> bool:
            return (
                    inspect.iscoroutinefunction(func) or
                    inspect.isasyncgenfunction(func) or
                    (hasattr(func, '__call__') and inspect.iscoroutinefunction(func.__call__))
            )
        try:
            self._logger.debug(f" # Step 1: check existed function")
            if not hasattr(instance, function_name):
                available_methods = [method for method in dir(instance)
                                     if not method.startswith('_') and callable(getattr(instance, method))]
                raise AttributeError(
                    f"function('{function_name}') is not exist in class. "
                    f"available functions: {available_methods}"
                )
            self._logger.debug(f" # Step 2: extract target function in dynamic-loader")
            target_function = getattr(instance, function_name)
            class_signature = inspect.signature(target_function)

            self._logger.debug(f" # Step 3: check callable function: '{function_name}'")
            if not callable(target_function):
                raise TypeError(f"'{function_name}'is not callable.")

            self._logger.debug(f" # Step 4: extract function pa: '{function_name}'")
            final_args, final_kwargs = self._process_arguments(args, kwargs, class_signature)

            self._logger.debug(f"# Step 5: check, method/function is async or sync: '{function_name}'")
            is_async = is_async_function(target_function)

            self._logger.debug(f"# Step 6: call function: '{function_name}'")
            if is_async:
                result = self._run_async_in_sync(target_function, *final_args, **final_kwargs)
            else:
                result = target_function(*final_args, **final_kwargs)
            return result

        except Exception as e:
            self._logger.error(f"failed execution({function_name}: {e}")
            traceback.print_exc()
            raise

    def call_module_function(self, module_path, function_name, *args, **kwargs) -> Any:
        try:
            self._logger.debug(f" # Step 1: load class module ({module_path}")
            module = self._load_module(module_path)

            self._logger.debug(f" # Step 2: check existed module-function")
            if not hasattr(module, function_name):
                available_functions = self.get_module_functions(module)
                raise AttributeError(
                    f"function '{function_name}' is not exit in '{function_name}'."
                    f"available functions: {available_functions}"
                )

            self._logger.debug(f" # Step 3: extract target module-function in dynamic-loader")
            target_function = getattr(module, function_name)

            self._logger.debug(f" # Step 4: check callable module-function: '{function_name}'")
            if not callable(target_function):
                raise TypeError(f"'{function_name}'is not callable.")

            self._logger.debug(f" # Step 5: call module-function: '{function_name}'")
            result = target_function(*args, **kwargs)
            return result

        except Exception as e:
            self._logger.error(f"failed execution({module_path}.{function_name}: {e}")
            traceback.print_exc()
            raise

    def call_with_dict(self, param_dict: Dict[str, Any], instance=None) -> Any:
        return self.call_class_method(instance, param_dict)

    def call_with_kwargs(self, instance=None, **kwargs) -> Any:
        return self.call_class_method(instance, **kwargs)

    def call_with_args(self, instance=None, *args) -> Any:
        return self.call_class_method(instance, *args)

    def call_mixed(self, instance=None, *args, **kwargs) -> Any:
        return self.call_class_method(instance, *args, **kwargs)

    def smart_call(self, module_path, function_name, target_name, *args, **kwargs):
        module = self._load_module(module_path)

        if hasattr(module, target_name):
            target = getattr(module, target_name)

            if inspect.isclass(target):
                instance = self.create_instance(module_path, target_name)
                result = self.call_class_method(instance, function_name, *args, **kwargs)
                return result
            elif callable(target):
                result = self.call_module_function(module_path, target_name, *args, **kwargs)
                return result
        raise ValueError(f"{target_name} is not found.")