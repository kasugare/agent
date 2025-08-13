#!/usr/bin/env python
# -*- coding: utf-8 -*-

from input.rag_input import RagInput
from retrieve.rag_retrieve import RagRetrieve
from generate.rag_generate import RagGenerator
from output.rag_output import RagOutput

class Workflow:
    def __init__(self, logger):
        self._logger = logger

    def input(self, query: str) -> str:
        rag_input = RagInput(self._logger)
        query = rag_input.input(query)
        return query

    async def retrieve(self, query, top_k):
        rag_retrieve = RagRetrieve(self._logger)
        retrieved_documents, document_sources = await rag_retrieve.retrieve(query, top_k)
        return retrieved_documents, document_sources

    def generate_prompt(self, question, prompt_template, retrieved_documents):
        rag_generator = RagGenerator(self._logger)
        prompt = rag_generator.generate_prompt(question, prompt_template, retrieved_documents)
        return prompt

    async def generate_answer(self, prompt, llm_type, model_name, base_url, temperature, api_key):
        rag_generator = RagGenerator(self._logger)
        answer = await rag_generator.generate_answer(prompt, llm_type, model_name, base_url, temperature, api_key)
        return answer

    def output(self, output_prompt, answer):
        rag_output = RagOutput(self._logger)
        output = rag_output.output(output_prompt, answer)
        return output

    async def run(self):
        self._logger.error("# Step 1: Set input params -> query")
        query = "에이전트의 기본 구성 요소는?"
        question = self.input(query)

        self._logger.error("# Step 2: Retrieve")
        retrieved_documents, document_sources = await self.retrieve(query=question, top_k=5)

        self._logger.error("# Step 3: Generate prompt")
        prompt_template = "다음 Context를 참고하여 질문에 한국어로 답하세요 \n 질문 : {{question}} \n Context : {{docs | join('\n')}}"
        prompt = self.generate_prompt(question, prompt_template, retrieved_documents)

        self._logger.error("# Step 4: Generate answer")
        serving_type = "openai"
        temperature = 0.8
        model_name = "gemma3:12b"
        url = "http://192.15.90.108:21434/v1"
        api_key = "dummy"
        answer = await self.generate_answer(prompt, llm_type=serving_type, model_name=model_name, base_url=url, temperature=temperature, api_key=api_key)

        self._logger.error("# Step 5: Output")
        output_prompt = "{{answer}}"
        result = self.output(output_prompt, answer)
        return result
