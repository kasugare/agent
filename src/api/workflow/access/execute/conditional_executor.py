#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Any, Dict, List, Optional
import re


class ConditionalExecutor:
    def __init__(self, logger):
        self._logger = logger
        self._env_params = {}
        self._asset_params = {}
        self._params = None
        self._target_handler = {}

    def set_env(self, env_params):
        self._env_params = env_params

    def set_params(self, params):
        self._params = params

    def set_asset(self, asset_params):
        self._asset_params = asset_params

    def set_target_handler(self, target_handler):
        self._target_handler = target_handler

    def _remove_duplicate_dicts(self, actions):
        seen = set()
        unique_actions = []

        for action in actions:
            action_tuple = tuple(sorted(action.items()))
            if action_tuple not in seen:
                seen.add(action_tuple)
                unique_actions.append(action)
        return unique_actions

    def run(self):
        if self._target_handler.get("type") != "conditional":
            raise ValueError("target_handler type must be 'conditional'")

        conditions = self._target_handler.get("conditions", {})
        branches = conditions.get("branches", [])

        for branch in branches:
            branch_type = branch.get("type")
            rules = branch.get("rules", [])
            logic = branch.get("logic", None)
            actionable = False

            if branch_type.lower() in ['if', 'elif']:
                if self._evaluate_condition(rules, logic):
                    actionable = True
            elif branch_type.lower() == "else":
                actionable = True
            else:
                raise ValueError("target_handler has not condition_rule")

            if actionable:
                actions = branch.get("actions", [])
                actions = self._remove_duplicate_dicts(actions)
                result = {"actions": actions}
                return result
        return None

    def _evaluate_condition(self, rules: List, logic) -> bool:
        if logic == "AND":
            result = all(self._evaluate_single_rule(rule) for rule in rules)

        elif logic == "OR":
            result = any(self._evaluate_single_rule(rule) for rule in rules)
        else:
            if len(rules) == 0:
                rule = rules[0]
                result = self._evaluate_single_rule(rule)
            else:
                raise ValueError("target_handler has not condition_rule")
        return result

    def _evaluate_single_rule(self, rule: Dict) -> bool:
        """단일 규칙 평가"""
        var_value = rule.get("variable")
        operator = rule.get("operator")
        value = rule.get("value")

        # check exsit
        if operator == "exist":
            return var_value is not None
        elif operator == "not_exist":
            return var_value is None

        # calculat conditions
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