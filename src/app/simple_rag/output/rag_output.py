#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .output_template_converter import OutputTemplateConverter


class RagOutput:
    def __init__(self, logger, asset_info):
        self._logger = logger
        self._set_asset(**asset_info)

    def _set_asset(self):
        None

    def output(self, output_templates: dict, output_context: dict={}):
        try:
            output_template = ("\n").join(output_templates.values())
            template_converter = OutputTemplateConverter(self._logger)

            req_variables = template_converter.extract_required_variables(output_template)
            self._logger.debug(f" - req_variables: {req_variables}")

            missing_vars = template_converter.validate(req_variables, output_context)
            if missing_vars:
                self._logger.warning(f"Missing variables: {missing_vars}")
                raise ValueError(f"Required variables not provided: {missing_vars}")

            answer = template_converter.render(output_template, output_context)
            self._logger.info("Prompt generated successfully")
        except Exception as e:
            self._logger.error(f"Failed to generate prompt: {str(e)}")
            raise
        return answer
