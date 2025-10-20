#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Generation:
    def __init__(self, model_type, llm_id, llm_params, prompt_template):
        self._model_type = model_type
        self._llm_id = llm_id
        self._llm_params = llm_params
        self._prompt_template = prompt_template

    def generate(self, question, docs):
        print(f"From the generation: {self._prompt_template}")
        answer = f"{question}({docs})"
        return answer