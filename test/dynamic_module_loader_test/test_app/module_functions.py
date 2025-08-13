# -*- coding: utf-8 -*-
#!/usr/bin/env python

from typing import Any, Dict, List, Optional, Union


def simple_add(a: int, b: int) -> int:
    """두 수를 더하는 간단한 함수"""
    result = a + b
    print(f"simple_add: {a} + {b} = {result}")
    return result


def complex_calculation(numbers: List[Union[int, float]], operation: str = "sum") -> Union[int, float]:
    """복잡한 계산을 수행하는 함수"""
    if not numbers:
        return 0

    operations = {
        "sum": sum,
        "product": lambda x: 1 if not x else x[0] if len(x) == 1 else x[0] * complex_calculation(x[1:], "product"),
        "average": lambda x: sum(x) / len(x),
        "max": max,
        "min": min
    }

    if operation not in operations:
        raise ValueError(f"지원하지 않는 연산: {operation}")

    result = operations[operation](numbers)
    print(f"complex_calculation: {operation}({numbers}) = {result}")
    return result


def string_processor(text: str, action: str = "upper", **kwargs) -> str:
    """문자열을 처리하는 함수"""
    actions = {
        "upper": lambda s: s.upper(),
        "lower": lambda s: s.lower(),
        "reverse": lambda s: s[::-1],
        "replace": lambda s: s.replace(kwargs.get("old", ""), kwargs.get("new", "")),
        "repeat": lambda s: s * kwargs.get("count", 1)
    }

    if action not in actions:
        raise ValueError(f"지원하지 않는 액션: {action}")

    result = actions[action](text)
    print(f"string_processor: {action}('{text}') = '{result}'")
    return result


def data_analyzer(data: List[Any], filters: Dict[str, Any] = None) -> Dict[str, Any]:
    """데이터를 분석하는 함수"""
    if filters is None:
        filters = {}

    # 필터 적용
    filtered_data = data
    if "type" in filters:
        filtered_data = [item for item in filtered_data if type(item).__name__ == filters["type"]]
    if "min_value" in filters:
        filtered_data = [item for item in filtered_data if isinstance(item, (int, float)) and item >= filters["min_value"]]
    if "max_value" in filters:
        filtered_data = [item for item in filtered_data if isinstance(item, (int, float)) and item <= filters["max_value"]]

    # 분석 결과
    numeric_data = [item for item in filtered_data if isinstance(item, (int, float))]
    string_data = [item for item in filtered_data if isinstance(item, str)]

    analysis = {
        "total_count": len(data),
        "filtered_count": len(filtered_data),
        "numeric_count": len(numeric_data),
        "string_count": len(string_data),
        "numeric_sum": sum(numeric_data) if numeric_data else 0,
        "numeric_avg": sum(numeric_data) / len(numeric_data) if numeric_data else 0,
        "unique_strings": list(set(string_data)) if string_data else []
    }

    print(f"data_analyzer: 분석 완료 - {analysis}")
    return analysis