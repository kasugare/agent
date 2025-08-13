# -*- coding: utf-8 -*-
#!/usr/bin/env python

# dynamic_loader.py - 동적 모듈 로더 및 함수 호출기

import importlib
import inspect
from typing import Any, Dict, List, Optional, Union
import traceback


class DynamicModuleLoader:
    def __init__(self):
        self.loaded_modules = {}
        self.created_instances = {}

    def load_module(self, module_path: str, reload: bool = False) -> Any:
        """ module_path: "app.test.test_class" """
        try:
            if module_path in self.loaded_modules and not reload:
                return self.loaded_modules[module_path]

            module = importlib.import_module(module_path)

            if reload:
                module = importlib.reload(module)

            self.loaded_modules[module_path] = module
            print(f"[INFO] 모듈 로드 성공: {module_path}")
            return module

        except ImportError as e:
            print(f"[ERROR] 모듈 로드 실패: {module_path} - {e}")
            raise
        except Exception as e:
            print(f"[ERROR] 예상치 못한 오류: {e}")
            raise

    def get_function_info(self, instance: Any, function_name: str) -> Dict[str, Any]:
        try:
            if not hasattr(instance, function_name):
                return {"error": f"함수 '{function_name}'이 존재하지 않습니다."}

            target_function = getattr(instance, function_name)

            if not callable(target_function):
                return {"error": f"'{function_name}'은 호출 가능한 함수가 아닙니다."}

            # 함수 시그니처 정보
            sig = inspect.signature(target_function)

            return {
                "name": function_name,
                "signature": str(sig),
                "parameters": {
                    param.name: {
                        "annotation": param.annotation if param.annotation != param.empty else None,
                        "default": param.default if param.default != param.empty else None
                    }
                    for param in sig.parameters.values()
                },
                "doc": target_function.__doc__
            }

        except Exception as e:
            return {"error": f"함수 정보 조회 실패: {e}"}

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

    def get_module_function_info(self, module_path: str, function_name: str) -> Dict[str, Any]:
        try:
            module = self.load_module(module_path)

            if not hasattr(module, function_name):
                return {"error": f"함수 '{function_name}'이 모듈 '{module_path}'에 존재하지 않습니다."}

            target_function = getattr(module, function_name)

            if not callable(target_function):
                return {"error": f"'{function_name}'은 호출 가능한 함수가 아닙니다."}

            # 클래스가 아닌 함수인지 확인
            if inspect.isclass(target_function):
                return {"error": f"'{function_name}'은 클래스입니다. call_module_function은 함수용입니다."}

            # 함수 시그니처 정보
            sig = inspect.signature(target_function)

            return {
                "name": function_name,
                "module": module_path,
                "signature": str(sig),
                "parameters": {
                    param.name: {
                        "annotation": param.annotation if param.annotation != param.empty else None,
                        "default": param.default if param.default != param.empty else None
                    }
                    for param in sig.parameters.values()
                },
                "doc": target_function.__doc__,
                "type": "module_function"
            }

        except Exception as e:
            return {"error": f"함수 정보 조회 실패: {e}"}

    def call_module_function(self, module_path: str, function_name: str, *args, **kwargs) -> Any:
        try:
            module = self.load_module(module_path)

            # 함수 존재 여부 확인
            if not hasattr(module, function_name):
                available_functions = self.get_module_functions(module)
                raise AttributeError(
                    f"함수 '{function_name}'이 모듈 '{module_path}'에 존재하지 않습니다. "
                    f"사용 가능한 함수: {available_functions}"
                )

            target_function = getattr(module, function_name)

            # 호출 가능한지 확인
            if not callable(target_function):
                raise TypeError(f"'{function_name}'은 호출 가능한 함수가 아닙니다.")

            # 함수 호출
            result = target_function(*args, **kwargs)
            print(f"[INFO] 모듈 함수 호출 성공: {module_path}.{function_name}")

            return result

        except Exception as e:
            print(f"[ERROR] 모듈 함수 호출 실패: {module_path}.{function_name} - {e}")
            traceback.print_exc()
            raise


    def call_function(self, instance: Any, function_name: str, *args, **kwargs) -> Any:
        try:
            # 함수 존재 여부 확인
            if not hasattr(instance, function_name):
                available_methods = [method for method in dir(instance)
                                     if not method.startswith('_') and callable(getattr(instance, method))]
                raise AttributeError(
                    f"함수 '{function_name}'이 존재하지 않습니다. "
                    f"사용 가능한 메서드: {available_methods}"
                )

            target_function = getattr(instance, function_name)

            # 호출 가능한지 확인
            if not callable(target_function):
                raise TypeError(f"'{function_name}'은 호출 가능한 함수가 아닙니다.")

            # 함수 호출
            result = target_function(*args, **kwargs)
            print(f"[INFO] 함수 호출 성공: {function_name}")

            return result

        except Exception as e:
            print(f"[ERROR] 함수 호출 실패: {function_name} - {e}")
            traceback.print_exc()
            raise

    def create_instance(self, module_path: str, class_name: str, init_params: Dict[str, Any] = None, instance_key: str = None) -> Any:
        try:
            if init_params is None:
                init_params = {}

            # 모듈 로드
            module = self.load_module(module_path)

            # 클래스 가져오기
            if not hasattr(module, class_name):
                raise AttributeError(f"클래스 '{class_name}'이 모듈 '{module_path}'에 존재하지 않습니다.")

            target_class = getattr(module, class_name)

            # 클래스인지 확인
            if not inspect.isclass(target_class):
                raise TypeError(f"'{class_name}'은 클래스가 아닙니다.")

            # 인스턴스 생성
            if isinstance(init_params, dict):
                instance = target_class(**init_params)
            else:
                instance = target_class(init_params)

            # 인스턴스 캐시
            if instance_key is None:
                instance_key = f"{module_path}.{class_name}"

            self.created_instances[instance_key] = instance
            print(f"[INFO] 인스턴스 생성 성공: {instance_key}")

            return instance

        except Exception as e:
            print(f"[ERROR] 인스턴스 생성 실패: {e}")
            traceback.print_exc()
            raise

    def execute_dynamic_call(self, module_path: str, class_name: str = None,
                             function_name: str = None, init_params: Dict[str, Any] = None,
                             function_args: tuple = (), function_kwargs: Dict[str, Any] = None) -> Any:
        if function_kwargs is None:
            function_kwargs = {}

        try:
            if class_name is None:
                # 모듈 레벨 함수 호출
                result = self.call_module_function(module_path, function_name, *function_args, **function_kwargs)
            else:
                # 클래스 메서드 호출
                instance = self.create_instance(module_path, class_name, init_params)
                result = self.call_function(instance, function_name, *function_args, **function_kwargs)

            return result

        except Exception as e:
            print(f"[ERROR] 동적 호출 실패: {e}")
            raise

    def inspect_module(self, module_path: str) -> Dict[str, Any]:
        try:
            module = self.load_module(module_path)

            classes = []
            functions = []
            variables = []

            for name in dir(module):
                if name.startswith('_'):
                    continue

                obj = getattr(module, name)
                if inspect.isclass(obj): # class
                    methods = [method for method in dir(obj)
                               if not method.startswith('_') and callable(getattr(obj, method))]
                    classes.append({
                        "name": name,
                        "methods": methods,
                        "doc": obj.__doc__
                    })
                elif callable(obj): # function
                    sig = inspect.signature(obj)
                    functions.append({
                        "name": name,
                        "signature": str(sig),
                        "doc": obj.__doc__
                    })
                else: # variables
                    variables.append({
                        "name": name,
                        "type": type(obj).__name__,
                        "value": str(obj) if len(str(obj)) < 100 else f"{str(obj)[:100]}..."
                    })

            module_info = {
                "module_path": module_path,
                "classes": classes,
                "functions": functions,
                "variables": variables
            }
            return module_info

        except Exception as e:
            return {"error": f"모듈 분석 실패: {e}"}

    def smart_call(self, module_path, target_name, function_name, *args, **kwargs):
        module = self.load_module(module_path)

        if hasattr(module, target_name):
            target = getattr(module, target_name)

            if inspect.isclass(target):
                instance = self.create_instance(module_path, target_name)
                result = self.call_function(instance, function_name, *args, **kwargs)
                return result
            elif callable(target):
                result = self.call_module_function(module_path, target_name, *args, **kwargs)
                return result

        raise ValueError(f"{target_name}을 찾을 수 없습니다.")