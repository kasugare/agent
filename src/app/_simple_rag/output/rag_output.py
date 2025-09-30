#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .prompt_template import PromptTemplateEngine


class RagOutput:
    def __init__(self, logger):
        self._logger = logger

    def output(self, output_prompt, answer):
        prompt_template_engine = PromptTemplateEngine(output_prompt)
        output = prompt_template_engine.render({"answer": answer})
        return output