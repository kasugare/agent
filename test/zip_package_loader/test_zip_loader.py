#!/usr/bin/env python
# -*- coding: utf-8 -*-

import zipfile
import sys
from pathlib import Path


class ZipModuleLoader:
    """ZIP 파일에서 Python 모듈을 로드하는 간단한 클래스"""

    def __init__(self, zip_path: str):
        self.zip_path = Path(zip_path)
        print(f"ZIP 경로: {self.zip_path}")
        print(f"ZIP 파일 존재: {self.zip_path.exists()}")

    def check_zip_contents(self):
        """ZIP 파일 내용 확인"""
        try:
            with zipfile.ZipFile(self.zip_path, 'r') as zip_file:
                print("📦 ZIP 파일 내용:")
                for file_name in zip_file.namelist():
                    print(f"  - {file_name}")
        except Exception as e:
            print(f"❌ ZIP 파일 읽기 오류: {e}")

    def load_module(self, module_name: str, class_name: str):
        self.check_zip_contents()
        """ZIP 파일에서 모듈 로드"""
        try:
            # ZIP 파일을 sys.path에 추가
            zip_str_path = str(self.zip_path)
            if zip_str_path not in sys.path:
                sys.path.insert(0, zip_str_path)
                print(f"sys.path에 추가: {zip_str_path}")

            # 기존 모듈 제거 (재로드용)
            modules_to_remove = [key for key in sys.modules.keys() if key.startswith(module_name)]
            for mod in modules_to_remove:
                del sys.modules[mod]
                print(f"기존 모듈 제거: {mod}")

            # 여러 방법으로 시도
            module = None

            # 방법 1: 직접 import
            try:
                print(f"방법 1 시도: {module_name}")
                module = __import__(module_name, fromlist=[class_name])
                print(f"방법 1 성공: {module_name}")
            except ImportError as e1:
                print(f"방법 1 실패: {e1}")

                # 방법 2: fromlist 없이
                try:
                    print(f"방법 2 시도: {module_name}")
                    parts = module_name.split('.')
                    module = __import__(module_name)
                    for part in parts[1:]:
                        module = getattr(module, part)
                    print(f"방법 2 성공: {module_name}")
                except Exception as e2:
                    print(f"방법 2 실패: {e2}")

                    # 방법 3: importlib 사용
                    try:
                        import importlib
                        print(f"방법 3 시도: {module_name}")
                        module = importlib.import_module(module_name)
                        print(f"방법 3 성공: {module_name}")
                    except Exception as e3:
                        print(f"방법 3 실패: {e3}")

            if not module:
                print("❌ 모든 import 방법 실패")
                return None

            # 클래스 가져오기
            if hasattr(module, class_name):
                app_class = getattr(module, class_name)
                print(f"클래스 가져오기 성공: {class_name}")
            else:
                print(f"❌ 클래스 '{class_name}' 없음. 사용 가능한 속성: {dir(module)}")
                return None

            # 인스턴스 생성
            instance = app_class(None)
            print(f"인스턴스 생성 성공")

            # 메서드 호출
            result = instance.query_input("test")
            print(f"메서드 호출 성공: {result}")

            return result

        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")
            import traceback
            traceback.print_exc()
            return None


def main():
    """테스트 함수"""
    # 설정
    zip_path = "/Users/hanati/workspace/agent/nodes/simple_rag/input.zip"
    module_name = "input.rag_input"  # rag_input.py 파일
    class_name = "RagInput"

    # 로더 생성
    loader = ZipModuleLoader(zip_path)

    # input.zip에서 rag_input 모듈 로드
    result = loader.load_module(module_name, class_name)
    if result:
        print(f"✅ 최종 결과: {result}")
    else:
        print("❌ 실행 실패")


if __name__ == "__main__":
    main()