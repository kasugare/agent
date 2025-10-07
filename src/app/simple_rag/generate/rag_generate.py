#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .llm_loader import LanguageModelLoader


class RagGenerator:
    def __init__(self, logger, base_url, api_key, asset_info={}):
        self._logger = logger
        self._base_url = base_url
        self._api_key = api_key
        self._set_asset(**asset_info)

    def _set_asset(self):
        None

    # prev_prmpt+prev_ans  + (curr_prompt) ,....

    """
        [
            "--------------- 첫번째 저장 -----------------"
            {
                'role': 'user',
                'content': '첫번째 프롬프트", <-- prev prompt
            },
            {
                'role': 'assistant',
                'content': '첫번째 답변"
            },
            "--------------- + 두번째 질의 -----------------"
            {
                'role': 'user',
                'content': '두번째 프롬프트", <-- prev prompt
            },
        ]                
    """
    async def generate_answer(self, prompt, temperature):
        ## message list 생성의 제한값 필요
        model_loader = LanguageModelLoader(self._logger)
        llm = model_loader.load_llm(llm_type=llm_type, model=model_name, base_url=self._base_url, temperature=temperature, api_key=self._api_key)

        # answer = await llm.generate(prompt=prompt) # openaip_llm.py
        message = [
            # "--------------- 첫번째 저장 -----------------"
            {
                'role': 'user',
                'content': '첫번째 프롬프트", # <-- prev prompt
            },
            {
                'role': 'assistant',
                'content': '첫번째 답변"
            },
            # "--------------- + 두번째 질의 -----------------"
            {
                'role': 'user',
                'content': '두번째 프롬프트", # <-- prev prompt
            }
        ]
        answer = await llm.generate(message=message)
        self._logger.debug(answer)
        return answer['text']
