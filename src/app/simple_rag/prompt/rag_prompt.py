#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .prompt_template import PromptTemplateEngine


class RagPrompt:
    def __init__(self, logger, hdfs_addr, hdfs_id, asset_info={}):
        self._logger = logger
        self._set_asset(**asset_info)

    def _set_asset(self):
        pass

    async def generate_prompt(self, prompt_templates: dict, prompt_context: dict={}):
        try:
            prompt_template = ("\n").join(prompt_templates.values())
            prompt_engine = PromptTemplateEngine(self._logger)

            req_variables = prompt_engine.extract_required_variables(prompt_template)
            self._logger.debug(f" - req_variables: {req_variables}")
            missing_vars = prompt_engine.validate(req_variables, prompt_context)
            if missing_vars:
                self._logger.warning(f"Missing variables: {missing_vars}")
                raise ValueError(f"Required variables not provided: {missing_vars}")

            prompt = prompt_engine.render(prompt_template, prompt_context)
            self._logger.info("Prompt generated successfully")
        except Exception as e:
            self._logger.error(f"Failed to generate prompt: {str(e)}")
            raise
        return prompt
