#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .prompt_template import PromptTemplateEngine


class RagPrompt:
    def __init__(self, logger, asset_info={}):
        self._logger = logger

    def generate_prompt(self, prompt_templates: dict, question: str, retrieved_documents, prompt_context: dict={}):
        prompt_template = ("\n").join(prompt_templates.values())
        prompt_engine = PromptTemplateEngine(self._logger, prompt_template)
        req_variables = prompt_engine.extract_required_variables(prompt_template)
        prompt_engine.extract_required_variables(prompt_template)
        # prompt_context = {
        #     "question": question,
        #     "retrieved_documents": 'fdsajflkdjsaljf'
        #     # "docs": retrieved_documents
        # }
        prompt = prompt_engine.render(prompt_context)
        return prompt
