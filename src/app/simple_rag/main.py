#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
from flow import Workflow
from ailand.common.logger import Logger


async def main():
    params = {
        "input": {
            "input": {
                "query": "에이전트의 기본 구성 요소는?"
            }
        },
        "retrieve": {
            "input": {
                "query": "@input.query",
                "collection_id": "2",
                "top_k": 5
            }
        },
        "generate": {
            "input": {
                "question": "@input.query",
                "docs": "@retrieval.retrieved_documents"
            },
            "body": {
                "llm_id": "3",
                "llm_params": {
                    "temperature": "0.8"
                },
                "prompt_template": "다음 Context를 참고하여 질문에 한국어로 답하세요 \n 질문 : \n {{question}} \n Context : {{docs | join('\n')}}"
            }
        },
        "output": {
            "input": {
                "generate_answer": "@generate.answer"
            },
            "body": {
                "prompt": "{{answer}}"
            },
            "output": {
                "query": "@input.query",
                "answer": "@output.generate_answer",
                "docs": "@retrieve.retrieved_documents"
            }
        }
    }
    logger = Logger()
    logger.setLevel("DEBUG")
    workflow = Workflow(logger)
    result = await workflow.run()


if __name__ == "__main__":
    asyncio.run(main())
    # main()