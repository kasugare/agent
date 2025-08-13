# -*- coding: utf-8 -*-
#!/usr/bin/env python

from typing import Any, Dict, List, Optional, Union


class AdvancedCalculator:
    """고급 계산기 클래스"""

    def __init__(self, precision: int = 2):
        self.precision = precision
        self.history = []
        print(f"AdvancedCalculator 초기화됨 (정밀도: {precision})")

    def complex_calculation(self, formula: str, variables: Dict[str, float] = None) -> float:
        """복잡한 수식을 계산합니다."""
        if variables is None:
            variables = {}

        try:
            # 간단한 수식 평가 (실제로는 더 안전한 방법 사용 권장)
            for var, value in variables.items():
                formula = formula.replace(var, str(value))

            result = eval(formula)  # 주의: 실제 운영에서는 ast.literal_eval 등 사용
            result = round(result, self.precision)

            self.history.append({"formula": formula, "result": result})
            print(f"수식 계산: {formula} = {result}")

            return result

        except Exception as e:
            raise ValueError(f"수식 계산 오류: {e}")

    def get_history(self) -> List[Dict[str, Any]]:
        """계산 히스토리를 반환합니다."""
        return self.history