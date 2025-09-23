#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .prompt_template import PromptTemplateEngine
from .llm_loader import LanguageModelLoader

class RagGenerator:
    def __init__(self, logger, api_key):
        self._logger = logger
        self._api_key = api_key

    def generate_prompt(self, question, prompt_template, retrieved_documents):
        prompt_template_engine = PromptTemplateEngine(prompt_template)
        prompt_context = {
            "question": question,
            "docs": retrieved_documents
        }
        prompt = prompt_template_engine.render(prompt_context)
        return prompt

    async def generate_answer(self, prompt, llm_type, model_name, base_url, temperature):
        model_loader = LanguageModelLoader(self._logger)
        llm = model_loader.load_llm(llm_type=llm_type, model= model_name, base_url=base_url, temperature=temperature, api_key=self._api_key)
        answer = await llm.generate(prompt=prompt)
        self._logger.debug(answer)
        return answer['text']

    def output(self, output_prompt, answer):
        prompt_template_engine = PromptTemplateEngine(output_prompt)
        output = prompt_template_engine.render({"answer": answer})
        return output

    async def generate_all(self, question, prompt_template, retrieved_documents, output_prompt, llm_type, model, base_url, temperature):
        prompt = self.generate_prompt(question, prompt_template, retrieved_documents)
        answer = await self.generate_answer(prompt, llm_type, model, base_url, temperature, self._api_key)
        output = self.output(output_prompt, answer)
        return output