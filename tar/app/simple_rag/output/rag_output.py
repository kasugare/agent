#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .prompt_template import PromptTemplateEngine


class RagOutput:
    def __init__(self, logger, asset_info):
        self._logger = logger
        self._set_asset(**asset_info)

    def _set_asset(self):
        None

    def output(self, output_prompt, answer):
        prompt_template_engine = PromptTemplateEngine(output_prompt)
        output = prompt_template_engine.render({"answer": answer})
        return output