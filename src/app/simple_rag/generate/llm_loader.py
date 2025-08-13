#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .openai_llm import OpenAICompatibleLLM


class LanguageModelLoader:
    def __init__(self, logger):
        self._logger = logger

    def load_llm(self, llm_type: str="ollama", model='gemma3', base_url='http://ailand.ai:30804/v1', temperature=0.7, api_key='dummy'):
        llm_type = llm_type.lower()
        if llm_type == "api":
            return ""
        elif llm_type == "openai":
            llm = OpenAICompatibleLLM(self._logger, model=model, base_url=base_url, temperature=temperature, api_key=api_key)
            return llm
        else:
            raise ValueError(f"Unsupported LLM type: {llm_type}")
