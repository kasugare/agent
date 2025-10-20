#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .llm_loader import LanguageModelLoader


class RagGenerator:
    def __init__(self, logger, asset_info={}):
        self._logger = logger
        self._set_asset(**asset_info)

    def _set_asset(self, model_id, llm_type, model_name, base_url, api_key):
        self._llm_type = llm_type
        self._model_name = model_name
        self._base_url = base_url
        self._api_key = api_key

    async def generate_answer(self, prompt, temperature, max_tokens, messages=None):
        model_loader = LanguageModelLoader(self._logger)
        llm = model_loader.load_llm(llm_type=self._llm_type, model=self._model_name, base_url=self._base_url, temperature=temperature, max_tokens=max_tokens, api_key=self._api_key)
        req_message = {
            'role': 'user',
            'content': prompt
        }

        if not messages:
            messages = [req_message]
        else:
            messages.append(req_message)

        answer = await llm.generate(messages=messages)
        self._logger.debug(answer)
        answer_conext = {
            'role': 'assistant',
            'content': answer.get('text')
        }
        messages.append(answer_conext)
        return answer, messages