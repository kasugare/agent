#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List, Any
from jinja2 import Environment, meta, StrictUndefined


class PromptTemplateEngine:
    def __init__(self, logger):
        self._logger = logger
        self._jinja_env = Environment(undefined=StrictUndefined)

    def extract_required_variables(self, prompt_template: str) -> List[str]:
        parsed_content = self._jinja_env.parse(prompt_template)
        return sorted(meta.find_undeclared_variables(parsed_content))

    def validate(self, required_vars, prompt_context: Dict[str, Any]) -> List[str]:
        missing_vars = [var for var in required_vars if var not in prompt_context]
        return missing_vars

    def render(self, prompt_template: str, prompt_context: Dict[str, Any]) -> str:
        self._template = self._jinja_env.from_string(prompt_template)
        return self._template.render(prompt_context)
