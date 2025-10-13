#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List, Any
from jinja2 import Environment, meta, StrictUndefined


class PromptTemplateEngine:
    def __init__(self, template_str: str):
        self._env = Environment(undefined=StrictUndefined)
        self._template = self._env.from_string(template_str)
        self._required_vars = self._extract_required_variables(template_str)

    def _extract_required_variables(self, template_str: str) -> List[str]:
        parsed_content = self._env.parse(template_str)
        return sorted(meta.find_undeclared_variables(parsed_content))

    def validate(self, variables: Dict[str, Any]) -> List[str]:
        """부족한 변수 목록 반환"""
        missing = [var for var in self._required_vars if var not in variables]
        return missing

    def render(self, context: Dict[str, Any]) -> str:
        return self._template.render(**context)
