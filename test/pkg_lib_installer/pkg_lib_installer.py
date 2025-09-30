#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import traceback
import inspect
import zipfile
import sys

class PkgLibInstaller:
    def __init__(self, zip_path=None):
        if not zip_path:
            zip_path = "/Users/hanati/workspace/agent/nodes/simple_rag/input.zip"
        self._zip_path = Path(zip_path)

    def _set_zip_path(self):
        zip_str_path = str(self._zip_path)
        if zip_str_path not in sys.path:
            sys.path.insert(0, zip_str_path)

    def _check_dup_module(self, module_name):
        modules_to_remove = [key for key in sys.modules.keys() if key.startswith(module_name)]
        for mod in modules_to_remove:
            del sys.modules[mod]
            print(f"기존 모듈 제거: {mod}")

    def _check_zip_contents(self):
        try:
            with zipfile.ZipFile(self._zip_path, 'r') as zip_file:
                print("📦 ZIP 파일 내용:")
                for file_name in zip_file.namelist():
                    print(f"  - {file_name}")
        except Exception as e:
            print(e)

    def _load_module(self, module_name: str, class_name: str):
        try:
            module = __import__(module_name, fromlist=[class_name])
            return module
        except Exception as e:
            print(e)

    def _create_class_instance(self, module, class_name: str, class_envs: dict):
        try:
            if hasattr(module, class_name):
                app_class = getattr(module, class_name)
                print(f"클래스 가져오기 성공: {class_name}")
            else:
                print(f"❌ 클래스 '{class_name}' 없음. 사용 가능한 속성: {dir(module)}")
                return None
            instance = app_class(**class_envs)
            return instance

        except Exception as e:
            traceback.print_exc()
        return None

    def _run_method(self, instance, method_name, params):
        def extract_method_params(method_signature):
            method_params = {
                param.name: {
                    "annotation": param.annotation if param.annotation != param.empty else None,
                    "default": param.default if param.default != param.empty else None
                }
                for param in method_signature.parameters.values()
            }
            return method_params

        target_method = getattr(instance, method_name)
        result = target_method(params)

        print(f"메서드 호출 성공: {result}")
        return result


    def do_process(self):
        zip_path = "/Users/hanati/workspace/agent/nodes/simple_rag/input.zip"
        module_name = "input.rag_input"
        class_name = "RagInput"
        class_envs = {"logger":"None"}
        method_name = "query_input"

        self._set_zip_path()
        self._check_zip_contents()
        self._check_dup_module(module_name)

        module = self._load_module(module_name, class_name)
        instance = self._create_class_instance(module, class_name, class_envs)
        result = self._run_method(instance, method_name, "hi")
        print(result)

if __name__ == "__main__":
    pkg_installer = PkgLibInstaller()
    pkg_installer.do_process()