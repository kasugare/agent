#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List, Any
from jinja2 import Environment, meta, StrictUndefined


class PromptTemplateEngine:
    def __init__(self, logger, prompt_template: str):
        self._logger = logger
        self._prompt_template = prompt_template
        self._jinja_env = Environment(undefined=StrictUndefined)
        self._template = self._jinja_env.from_string(prompt_template)
        # self._required_vars = self.extract_required_variables(prompt_template)

    def extract_required_variables(self, prompt_template: str) -> List[str]:
        parsed_content = self._jinja_env.parse(prompt_template)
        return sorted(meta.find_undeclared_variables(parsed_content))

    def validate(self, required_vars, variables: Dict[str, Any]) -> List[str]:
        """부족한 변수 목록 반환"""
        missing_vars = [var for var in required_vars if var not in variables]
        return missing_vars

    def render(self, prompt_context: Dict[str, Any]) -> str:
        return self._template.render(prompt_context)
