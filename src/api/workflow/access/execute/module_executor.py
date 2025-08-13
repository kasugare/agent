#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Any, Dict, List, Optional, Union
from api.workflow.common.util_dynamic_loader import DynamicLoader
from concurrent.futures import ThreadPoolExecutor
import traceback
import inspect
import asyncio


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

    def _run_async_method_in_new_loop(self, async_method, *args, **kwargs) -> Any:
        return asyncio.run(self._call_async_method(async_method, *args, **kwargs))

    async def _call_async_method(self, method, *args, **kwargs):
        self._logger.debug(f"Calling async method: {method.__name__}")
        result = await method(*args, **kwargs)
        return result

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
            self._logger.debug(f" - {self._function_name}: Event loop is already running, using thread executor")
            with ThreadPoolExecutor() as executor:
                future = executor.submit(self._run_async_method_in_new_loop, async_method, *args, **kwargs)
                result = future.result()
        except RuntimeError:
            result = asyncio.run(self._call_async_method(async_method, *args, **kwargs))
        return result

    def _process_arguments(self, args: tuple, kwargs: dict, signature: inspect.Signature) -> tuple:
        final_args = []
        final_kwargs = {}

        params = list(signature.parameters.values())
        param_names = [p.name for p in params if p.name != 'self']

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

    def call_with_dict(self, param_dict: Dict[str, Any], instance=None) -> Any:
        return self._call_class_method(instance, param_dict)

    def call_with_kwargs(self, instance=None, **kwargs) -> Any:
        return self._call_class_method(instance, **kwargs)

    def call_with_args(self, instance=None, *args) -> Any:
        return self._call_class_method(instance, *args)

    def call_mixed(self, instance=None, *args, **kwargs) -> Any:
        return self._call_class_method(instance, *args, **kwargs)

    def _execute_dynamic_call(self, function_name: str = None, init_params: Dict[str, Any] = None,
                             function_args: tuple = (), function_kwargs: Dict[str, Any] = None) -> Any:
        if function_kwargs is None:
            function_kwargs = {}

        try:
            if self._class_name is None:
                result = self._call_module_function(self._module_path, function_name, *function_args, **function_kwargs)
            else:
                instance = self.create_instance(self._module_path, self._class_name, self._env_params)
                result = self._call_class_method(instance, function_name, *function_args, **function_kwargs)
        except Exception as e:
            self._logger.error(f"failed execution({self._class_name}.{function_name}: {e}")
            raise
        return result

    def _smart_call(self, target_name, function_name, *args, **kwargs):
        module = self._load_module(self._module_path)

        if hasattr(module, target_name):
            target = getattr(module, target_name)

            if inspect.isclass(target):
                instance = self.create_instance(self._module_path, target_name)
                result = self._call_class_method(instance, function_name, *args, **kwargs)
                return result
            elif callable(target):
                result = self._call_module_function(self._module_path, target_name, *args, **kwargs)
                return result
        raise ValueError(f"{target_name} is not found.")

    def _call_class_method(self, instance, *args, **kwargs) -> Any:
        def is_async_function(func) -> bool:
            return (
                    inspect.iscoroutinefunction(func) or
                    inspect.isasyncgenfunction(func) or
                    (hasattr(func, '__call__') and inspect.iscoroutinefunction(func.__call__))
            )
        try:
            if not instance:
                instance = self.create_instance(self._module_path, self._class_name, *self._env_params)

            self._logger.debug(f" # Step 1: check existed function")
            if not hasattr(instance, self._function_name):
                available_methods = [method for method in dir(instance)
                                     if not method.startswith('_') and callable(getattr(instance, method))]
                raise AttributeError(
                    f"function('{self._function_name}') is not exist in class. "
                    f"available functions: {available_methods}"
                )
            self._logger.debug(f" # Step 2: extract target function in dynamic-loader")
            target_function = getattr(instance, self._function_name)
            class_signature = inspect.signature(target_function)

            self._logger.debug(f" # Step 3: check callable function: '{self._function_name}'")
            if not callable(target_function):
                raise TypeError(f"'{self._function_name}'is not callable.")

            self._logger.debug(f" # Step 4: extract function pa: '{self._function_name}'")
            final_args, final_kwargs = self._process_arguments(args, kwargs, class_signature)

            self._logger.debug(f"# Step 5: check, method/function is async or sync: '{self._function_name}'")
            is_async = is_async_function(target_function)
            self._logger.error(f"   - {self._function_name} async mode?: {is_async}")

            self._logger.debug(f"# Step 6: call function: '{self._function_name}'")
            if is_async:
                result = self._run_async_in_sync(target_function, *final_args, **final_kwargs)
            else:
                result = target_function(*final_args, **final_kwargs)
            return result

        except Exception as e:
            self._logger.error(f"failed execution({self._function_name}: {e}")
            traceback.print_exc()
            raise

    def _call_module_function(self, *args, **kwargs) -> Any:
        try:
            self._logger.debug(f" # Step 1: load class module ({self._module_path}")
            module = self._load_module(self._module_path)

            self._logger.debug(f" # Step 2: check existed module-function")
            if not hasattr(module, self._function_name):
                available_functions = self.get_module_functions(module)
                raise AttributeError(
                    f"function '{self._function_name}' is not exit in '{self._function_name}'."
                    f"available functions: {available_functions}"
                )

            self._logger.debug(f" # Step 3: extract target module-function in dynamic-loader")
            target_function = getattr(module, self._function_name)

            self._logger.debug(f" # Step 4: check callable module-function: '{self._function_name}'")
            if not callable(target_function):
                raise TypeError(f"'{self._function_name}'is not callable.")

            self._logger.debug(f" # Step 5: call module-function: '{self._function_name}'")
            result = target_function(*args, **kwargs)
            return result

        except Exception as e:
            self._logger.error(f"failed execution({self._module_path}.{self._function_name}: {e}")
            traceback.print_exc()
            raise

    def run(self, *args, **kwargs):
        try:
            if self._class_name:
                instance = self.create_instance(self._module_path, self._class_name, self._env_params)
                result = self._call_class_method(instance, *args, **kwargs)
            else:
                result = self._call_module_function(*args, **kwargs)
        except Exception as e:
            self._logger.error(e)
            raise RuntimeError
        return result