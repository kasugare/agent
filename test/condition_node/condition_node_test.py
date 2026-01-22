from typing import Any, Dict, List, Optional
import re


class ConditionNodeExecutor:
    """Condition Node를 평가하고 실행하는 클래스"""

    def __init__(self, workflow_context: Dict[str, Any]):
        """
        Args:
            workflow_context: 전체 워크플로우의 변수를 저장하는 컨텍스트
                             예: {"NODE_A.test_result": 10, "NODE_A.status": "ready"}
        """
        self.context = workflow_context

    def execute(self, edge_config: Dict) -> str:
        """
        Condition Node의 edge 설정을 실행

        Args:
            edge_config: edge 설정 딕셔너리

        Returns:
            다음 실행할 노드 이름 (target)
        """
        target_handler = edge_config.get("target_handler", {})

        if target_handler.get("type") != "conditional":
            raise ValueError("target_handler type must be 'conditional'")

        conditions = target_handler.get("conditions", {})
        branches = conditions.get("branches", [])

        # branches 순회하며 조건 평가
        for branch in branches:
            branch_type = branch.get("type")

            if branch_type == "else":
                # else는 무조건 실행
                self._execute_actions(branch.get("actions", []))
                return branch.get("target")

            # if, elif 조건 평가
            condition = branch.get("condition", {})
            if self._evaluate_condition(condition):
                # 조건이 참이면 actions 실행 후 target 반환
                self._execute_actions(branch.get("actions", []))
                return branch.get("target")

        # 모든 조건이 false이고 else도 없으면 None
        return None

    def _evaluate_condition(self, condition: Dict) -> bool:
        """조건을 평가"""
        logic = condition.get("logic")

        if logic == "AND":
            rules = condition.get("rules", [])
            return all(self._evaluate_single_rule(rule) for rule in rules)

        elif logic == "OR":
            rules = condition.get("rules", [])
            return any(self._evaluate_single_rule(rule) for rule in rules)

        else:
            # 단일 조건
            return self._evaluate_single_rule(condition)

    def _evaluate_single_rule(self, rule: Dict) -> bool:
        """단일 규칙 평가"""
        variable = rule.get("variable")
        operator = rule.get("operator")
        value = rule.get("value")

        # context에서 변수 값 가져오기
        var_value = self._get_variable(variable)

        # 존재 여부 체크
        if operator == "exist":
            return var_value is not None

        if operator == "not_exist":
            return var_value is None

        # 비교 연산
        if operator == ">":
            return var_value > value
        elif operator == "<":
            return var_value < value
        elif operator == ">=":
            return var_value >= value
        elif operator == "<=":
            return var_value <= value
        elif operator == "==":
            return var_value == value
        elif operator == "!=":
            return var_value != value

        return False

    def _execute_actions(self, actions: List[Dict]) -> None:
        """actions 실행"""
        for action in actions:
            action_type = action.get("type")
            variable = action.get("variable")
            value = action.get("value")

            if action_type == "set_variable":
                self._set_variable(variable, value)

            elif action_type == "increment":
                current = self._get_variable(variable) or 0
                self._set_variable(variable, current + value)

            elif action_type == "decrement":
                current = self._get_variable(variable) or 0
                self._set_variable(variable, current - value)

            elif action_type == "calculate":
                expression = action.get("expression")
                result = self._evaluate_expression(expression)
                self._set_variable(variable, result)

            elif action_type == "copy_variable":
                source_value = self._get_variable(value)
                self._set_variable(variable, source_value)

            elif action_type == "delete_variable":
                self._delete_variable(variable)

    def _get_variable(self, variable_name: str) -> Any:
        """context에서 변수 가져오기"""
        return self.context.get(variable_name)

    def _set_variable(self, variable_name: str, value: Any) -> None:
        """context에 변수 설정"""
        # value가 다른 변수를 참조하는 경우
        if isinstance(value, str) and value in self.context:
            value = self.context[value]

        self.context[variable_name] = value

    def _delete_variable(self, variable_name: str) -> None:
        """context에서 변수 삭제"""
        if variable_name in self.context:
            del self.context[variable_name]

    def _evaluate_expression(self, expression: str) -> Any:
        """수식 계산 (간단한 구현)"""
        # 변수를 실제 값으로 치환
        for var_name, var_value in self.context.items():
            expression = expression.replace(var_name, str(var_value))

        # 안전한 eval (보안상 주의 필요)
        try:
            return eval(expression, {"__builtins__": {}}, {})
        except Exception as e:
            print(f"Expression evaluation error: {e}")
            return None


# 사용 예시
if __name__ == "__main__":
    # Workflow context 초기화
    context = {
        "NODE_A.test_result": 10,
        "NODE_A.status": "ready"
    }

    # Edge 설정
    edge_config = {
        "source": "NODE_A.process",
        "target": "CONDITION_NODE_1.evaluate",
        "target_handler": {
            "type": "conditional",
            "conditions": {
                "branches": [
                    {
                        "type": "if",
                        "condition": {
                            "variable": "NODE_A.test_result",
                            "operator": ">",
                            "value": 5
                        },
                        "actions": [
                            {
                                "type": "set_variable",
                                "variable": "NODE_A.test_result",
                                "value": 100
                            },
                            {
                                "type": "set_variable",
                                "variable": "NODE_A.status",
                                "value": "high"
                            }
                        ],
                        "target": "NODE_B.process"
                    },
                    {
                        "type": "else",
                        "actions": [
                            {
                                "type": "set_variable",
                                "variable": "NODE_A.test_result",
                                "value": 0
                            }
                        ],
                        "target": "NODE_C.process"
                    }
                ]
            }
        }
    }

    # Executor 생성 및 실행
    executor = ConditionNodeExecutor(context)

    print("Before execution:")
    print(f"  NODE_A.test_result = {context['NODE_A.test_result']}")
    print(f"  NODE_A.status = {context['NODE_A.status']}")

    next_node = executor.execute(edge_config)

    print("\nAfter execution:")
    print(f"  NODE_A.test_result = {context['NODE_A.test_result']}")
    print(f"  NODE_A.status = {context['NODE_A.status']}")
    print(f"  Next node: {next_node}")