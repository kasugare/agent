# -*- coding: utf-8 -*-
#!/usr/bin/env python

from dynamic_module_loader import DynamicModuleLoader
import traceback


class DynamicClassLoader:
    def __init__(self):
        pass

    def _test_module_1(self, loader):
        print("1. 기본 사용법")
        print("-" * 30)

        # 현재 모듈에서 TestClass 사용 (__main__ 모듈)
        module_path = "test_app.test_class"  # "__main__"  # 현재 스크립트
        class_name = "TestClass"

        # 초기화 파라미터
        init_params = {"config": {"name": "test_instance"}}

        # 인스턴스 생성
        instance = loader.create_instance(module_path, class_name, init_params)

        # 함수 호출
        loader.call_class_function(instance, "add_data", 10)
        loader.call_class_function(instance, "add_data", "hello")
        loader.call_class_function(instance, "add_data", 20)

        data = loader.call_class_function(instance, "get_data")
        print(f" - 저장된 데이터: {data}")

        processed = loader.call_class_function(instance, "process_data", multiplier=3)
        print(f" - 처리된 데이터: {processed}")

        calc_result = loader.call_class_function(instance, "calculate", 15, 5, operation="multiply")
        print(f" - 계산 결과: {calc_result}")

        print("\n" + "=" * 50 + "\n")

    def _test_module_2(self, loader):
        print("2. 한 번에 실행하기")
        print("-" * 30)

        result = loader.execute_dynamic_call(
            module_path="test_app.advanced_calculator",  # "__main__",
            class_name="AdvancedCalculator",
            function_name="complex_calculation",
            init_params={"precision": 3},
            function_args=("x**2 + y*3 + 10",),
            function_kwargs={"variables": {"x": 5, "y": 2}}
        )
        print(f"복잡한 계산 결과: {result}")
        print("\n" + "=" * 50 + "\n")

    def _test_module_3(self, loader, module_path, class_name):
        print("3. 함수 정보 조회")
        print("-" * 30)

        calc_instance = loader.create_instance(module_path, class_name)

        # 사용 가능한 메서드 목록
        methods = loader.get_available_methods(calc_instance)
        print(f"사용 가능한 메서드: {methods}")

        # 특정 함수 정보
        func_info = loader.get_function_info(calc_instance, "complex_calculation")
        print(f"함수 정보: {func_info}")
        print("\n" + "=" * 50 + "\n")

    def _test_module_4(self, loader, module_path, class_name):
        print("4. 동적 함수명으로 호출")
        print("-" * 30)

        test_instance = loader.create_instance(module_path, class_name)

        # 동적으로 받아온 함수명들
        dynamic_functions = ["add_data", "get_data", "process_data"]

        for func_name in dynamic_functions:
            try:
                if func_name == "add_data":
                    result = loader.call_function(test_instance, func_name, f"dynamic_data_{func_name}")
                elif func_name == "get_data":
                    result = loader.call_function(test_instance, func_name)
                    print(f"{func_name} 결과: {result}")
                elif func_name == "process_data":
                    result = loader.call_function(test_instance, func_name)
                    print(f"{func_name} 결과: {result}")

            except Exception as e:
                print(f"함수 '{func_name}' 호출 실패: {e}")

    def _test_module_5(self, loader, module_path, function_name, function_params):
        result = loader.execute_dynamic_call(
            module_path=module_path,
            class_name=None,  # 모듈 함수임을 명시
            function_name=function_name,
            function_args=function_params
        )
        return result

    def _test_module_6(self, loader, module_path, function_name):
        result = loader.call_module_function(module_path, function_name, 10, 20)
        return result

    def _test_module_7(self, loader, module_path, function_name, function_params):
        result = loader.call_module_function(module_path, function_name, function_params)
        return result

    def example_usage(self):
        """동적 모듈 로더 사용 예제"""

        loader = DynamicModuleLoader()

        print("=== 동적 모듈 로더 사용 예제 ===\n")

        try:
            # 예제 1: 기본 사용법
            self._test_module_1(loader)

            # 예제 2: 한 번에 실행하기
            self._test_module_2(loader)

            # 예제 3: 함수 정보 조회
            self._test_module_3(loader, module_path="test_app.test_class", class_name="TestClass")

            # 예제 4: 동적 함수명으로 호출
            # self._test_module_4(loader, module_path="test_app.advanced_calculator", class_name="AdvancedCalculator")

            # 예제 5: Module Function 1
            self._test_module_5(loader, module_path="test_app.math.math_functions", function_name="calculate_average", function_params=([1, 2, 3, 4, 5],))

            # 예제 6: Module Function 2
            result1 = self._test_module_6(loader, module_path="test_app.math.math_functions", function_name="add_numbers")

            # 예제 7: Module Function 3
            result2 = self._test_module_7(loader, module_path="test_app.math.math_functions", function_name="multiply_list", function_params=[2,3,4])

            # 예제 8: 클래스 메서드 호출
            result3 = loader.execute_dynamic_call(
                module_path="test_app.math.math_functions",
                class_name="AdvancedMath",
                function_name="power",
                function_args=(2, 8)
            )

            print(f"함수 결과: {result1}, {result2}")
            print(f"클래스 메서드 결과: {result3}")

            # 예제 9: 스마트 호출 (클래스/메소드 자동 인지)
            result1 = loader.smart_call("test_app.math.math_functions", "sqrt", None, 16)  # 모듈 함수
            result2 = loader.smart_call("test_app.math.calculator", "Calculator", "add", 10, 20)  # 클래스 메서드
            print(f" - 함수 결과: {result1}")
            print(f" - 클래스 메서드 결과: {result2}")


        except Exception as e:
            print(f"예제 실행 중 오류 발생: {e}")
            traceback.print_exc()


if __name__ == "__main__":
    class_loader = DynamicClassLoader()
    class_loader.example_usage()