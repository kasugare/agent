# -*- coding: utf-8 -*-
#!/usr/bin/env python

from typing import Any, Dict, List, Optional, Union

class TestClass:
    """테스트용 클래스"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.data = []
        print(f"TestClass 초기화됨: {self.config}")

    def add_data(self, item: Any) -> None:
        """데이터를 추가합니다."""
        self.data.append(item)
        print(f"데이터 추가됨: {item}")

    def get_data(self) -> List[Any]:
        """저장된 데이터를 반환합니다."""
        return self.data

    def process_data(self, multiplier: int = 2) -> List[Any]:
        """데이터를 처리합니다."""
        processed = []
        for item in self.data:
            if isinstance(item, (int, float)):
                processed.append(item * multiplier)
            else:
                processed.append(f"processed_{item}")
        return processed

    def calculate(self, a: int, b: int, operation: str = "add") -> Union[int, float]:
        """계산을 수행합니다."""
        operations = {
            "add": lambda x, y: x + y,
            "subtract": lambda x, y: x - y,
            "multiply": lambda x, y: x * y,
            "divide": lambda x, y: x / y if y != 0 else None
        }

        if operation in operations:
            result = operations[operation](a, b)
            print(f"계산 결과: {a} {operation} {b} = {result}")
            return result
        else:
            raise ValueError(f"지원하지 않는 연산: {operation}")

