#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import List, Dict, Any, Optional, Union, AsyncGenerator
from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from openai.types import Completion
from .base_llm import BaseLLM


class OpenAICompatibleLLM(BaseLLM):
    """
    OpenAI API 스펙을 따르는 모든 모델 서버에 대응하는 클래스

    지원하는 서버들:
    - OpenAI API
    - Triton Inference Server (OpenAI compatible mode)
    - vLLM Server
    - Text Generation Inference (TGI)
    - FastChat
    - LocalAI
    - Ollama (OpenAI compatible mode)
    - 기타 OpenAI API 스펙을 따르는 모든 서버
    """

    def __init__(self, logger, model: str, base_url: Optional[str] = None, api_key: Optional[str] = None, temperature: float = 0.7, **kwargs):
        """
        OpenAI 호환 LLM 클래스 초기화

        Args:
            model: 모델명 (예: "gpt-3.5-turbo", "llama-2-7b-chat")
            base_url: API 서버 URL (None이면 OpenAI 공식 API 사용)
            api_key: API 키 (로컬 서버의 경우 "dummy" 또는 None 가능)
            temperature: 생성 온도 (0.0-2.0)
            max_tokens: 최대 토큰 수
            timeout: 요청 타임아웃 (초)
            max_retries: 최대 재시도 횟수
            **kwargs: 추가 OpenAI 클라이언트 파라미터
        """
        super().__init__(logger)
        self._logger = logger
        self.model = model
        self.base_url = base_url
        self.api_key = api_key or "dummy"  # 로컬 서버용 더미 키
        self.temperature = temperature
        self.max_tokens = None
        self.timeout = 180.0
        self.max_retries = 3

        # OpenAI 클라이언트 초기화
        client_kwargs = {
            "api_key": self.api_key,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            **kwargs
        }

        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        # 동기/비동기 클라이언트 생성
        self.client = OpenAI(**client_kwargs)
        self.async_client = AsyncOpenAI(**client_kwargs)

        self._logger.debug(f"OpenAI Compatible LLM initialized: {self.model} @ {self.base_url or 'OpenAI'}")

    async def chat_completions_create(
            self,
            messages: List[Dict[str, str]],
            model: Optional[str] = None,
            temperature: Optional[float] = None,
            max_tokens: Optional[int] = None,
            top_p: Optional[float] = None,
            frequency_penalty: Optional[float] = None,
            presence_penalty: Optional[float] = None,
            stop: Optional[Union[str, List[str]]] = None,
            stream: bool = False,
            **kwargs
    ) -> Union[ChatCompletion, AsyncGenerator[ChatCompletionChunk, None]]:
        """
        채팅 완성 생성 (OpenAI chat.completions.create 호환)

        Args:
            messages: 채팅 메시지 리스트
            model: 모델명 (기본값: 초기화시 설정된 모델)
            temperature: 생성 온도
            max_tokens: 최대 토큰 수
            top_p: Top-p 샘플링
            frequency_penalty: 빈도 페널티
            presence_penalty: 존재 페널티
            stop: 중단 시퀀스
            stream: 스트리밍 여부
            **kwargs: 추가 파라미터

        Returns:
            ChatCompletion 객체 또는 스트리밍 제너레이터
        """
        # 파라미터 설정
        params = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "stream": stream
        }

        # 선택적 파라미터 추가
        if max_tokens is not None or self.max_tokens is not None:
            params["max_tokens"] = max_tokens or self.max_tokens
        if top_p is not None:
            params["top_p"] = top_p
        if frequency_penalty is not None:
            params["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            params["presence_penalty"] = presence_penalty
        if stop is not None:
            params["stop"] = stop

        # 추가 파라미터 병합
        params.update(kwargs)

        try:
            if stream:
                return await self.async_client.chat.completions.create(**params)
            else:
                return await self.async_client.chat.completions.create(**params)
        except Exception as e:
            self._logger.error(f"Chat completion error: {e}")
            raise

    async def completions_create(
            self,
            prompt: Union[str, List[str]],
            model: Optional[str] = None,
            temperature: Optional[float] = None,
            max_tokens: Optional[int] = None,
            top_p: Optional[float] = None,
            frequency_penalty: Optional[float] = None,
            presence_penalty: Optional[float] = None,
            stop: Optional[Union[str, List[str]]] = None,
            stream: bool = False,
            **kwargs
    ) -> Completion:
        """
        텍스트 완성 생성 (OpenAI completions.create 호환)

        Args:
            prompt: 입력 프롬프트
            model: 모델명
            temperature: 생성 온도
            max_tokens: 최대 토큰 수
            top_p: Top-p 샘플링
            frequency_penalty: 빈도 페널티
            presence_penalty: 존재 페널티
            stop: 중단 시퀀스
            stream: 스트리밍 여부
            **kwargs: 추가 파라미터

        Returns:
            Completion 객체
        """
        params = {
            "model": model or self.model,
            "prompt": prompt,
            "temperature": temperature if temperature is not None else self.temperature,
            "stream": stream
        }

        if max_tokens is not None or self.max_tokens is not None:
            params["max_tokens"] = max_tokens or self.max_tokens
        if top_p is not None:
            params["top_p"] = top_p
        if frequency_penalty is not None:
            params["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            params["presence_penalty"] = presence_penalty
        if stop is not None:
            params["stop"] = stop

        params.update(kwargs)

        try:
            return await self.async_client.completions.create(**params)
        except Exception as e:
            self._logger.error(f"Completion error: {e}")
            raise

    async def generate(self, prompt: str, stream: bool = False, **kwargs) -> dict:
        """
        BaseLLM 호환을 위한 generate 메서드

        Args:
            prompt: 입력 프롬프트
            stream: 스트리밍 여부
            **kwargs: 추가 파라미터

        Returns:
            생성 결과 딕셔너리
        """
        try:
            # 채팅 형식으로 변환하여 호출
            messages = [{"role": "user", "content": prompt}]

            completion = await self.chat_completions_create(
                messages=messages,
                stream=stream,
                **kwargs
            )

            if stream:
                # 스트리밍 모드의 경우 첫 번째 청크만 반환하거나 별도 처리 필요
                return {
                    "text": "[스트리밍 모드]",
                    "tokens": 0,
                    "model": self.model,
                    "stream": True
                }
            else:
                generated_text = completion.choices[0].message.content or ""
                return {
                    "text": generated_text,
                    "tokens": completion.usage.completion_tokens if completion.usage else len(generated_text.split()),
                    "model": completion.model,
                    "stream": False,
                    "usage": {
                        "prompt_tokens": completion.usage.prompt_tokens if completion.usage else 0,
                        "completion_tokens": completion.usage.completion_tokens if completion.usage else 0,
                        "total_tokens": completion.usage.total_tokens if completion.usage else 0
                    } if completion.usage else None
                }
        except Exception as e:
            self._logger.error(f"Generate method error: {e}")
            raise

    async def stream_chat(
            self,
            messages: List[Dict[str, str]],
            **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        스트리밍 채팅 제너레이터

        Args:
            messages: 채팅 메시지 리스트
            **kwargs: 추가 파라미터

        Yields:
            생성된 텍스트 청크들
        """
        try:
            stream = await self.chat_completions_create(
                messages=messages,
                stream=True,
                **kwargs
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            self._logger.error(f"Stream chat error: {e}")
            raise

    def get_available_models(self) -> List[str]:
        """
        사용 가능한 모델 목록 조회

        Returns:
            모델명 리스트
        """
        try:
            models = self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            self._logger.warning(f"Failed to get models list: {e}")
            return [self.model]  # 기본 모델만 반환

    async def get_available_models_async(self) -> List[str]:
        """
        사용 가능한 모델 목록 비동기 조회

        Returns:
            모델명 리스트
        """
        try:
            models = await self.async_client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            self._logger.warning(f"Failed to get models list: {e}")
            return [self.model]

    def set_model(self, model: str):
        """모델 변경"""
        self.model = model
        self._logger.info(f"Model changed to: {model}")

    def set_temperature(self, temperature: float):
        """온도 설정 변경"""
        if 0.0 <= temperature <= 2.0:
            self.temperature = temperature
            self._logger.info(f"Temperature changed to: {temperature}")
        else:
            raise ValueError("Temperature must be between 0.0 and 2.0")

    def set_max_tokens(self, max_tokens: int):
        """최대 토큰 수 변경"""
        if max_tokens > 0:
            self.max_tokens = max_tokens
            self._logger.info(f"Max tokens changed to: {max_tokens}")
        else:
            raise ValueError("Max tokens must be positive")

    async def health_check(self) -> bool:
        """
        서버 상태 확인

        Returns:
            서버 상태 (True: 정상, False: 비정상)
        """
        try:
            # 간단한 요청으로 서버 상태 확인
            await self.chat_completions_create(
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            self._logger.error(f"Health check failed: {e}")
            return False

    def __repr__(self) -> str:
        return f"OpenAICompatibleLLM(model='{self.model}', base_url='{self.base_url}')"


# 편의를 위한 팩토리 함수들
def create_openai_llm(model: str = "gpt-3.5-turbo", api_key: Optional[str] = None, **kwargs) -> OpenAICompatibleLLM:
    """OpenAI 공식 API용 LLM 생성"""
    return OpenAICompatibleLLM(model=model, api_key=api_key, **kwargs)


def create_vllm_llm(model: str, base_url: str = "http://localhost:8000", **kwargs) -> OpenAICompatibleLLM:
    """vLLM 서버용 LLM 생성"""
    return OpenAICompatibleLLM(
        model=model,
        base_url=base_url,
        api_key="dummy",
        **kwargs
    )


def create_triton_llm(model: str, base_url: str = "http://localhost:8000", **kwargs) -> OpenAICompatibleLLM:
    """Triton OpenAI 호환 모드용 LLM 생성"""
    return OpenAICompatibleLLM(
        model=model,
        base_url=f"{base_url}/v1",  # OpenAI 호환 엔드포인트
        api_key="dummy",
        **kwargs
    )


def create_local_llm(model: str, base_url: str, **kwargs) -> OpenAICompatibleLLM:
    """로컬 서버용 LLM 생성 (LocalAI, FastChat 등)"""
    return OpenAICompatibleLLM(
        model=model,
        base_url=base_url,
        api_key="dummy",
        **kwargs
    )


def create_ollama_llm(model: str, base_url: str = "http://localhost:11434", **kwargs) -> OpenAICompatibleLLM:
    """Ollama OpenAI 호환 모드용 LLM 생성"""
    return OpenAICompatibleLLM(
        model=model,
        base_url=f"{base_url}/v1",
        api_key="dummy",
        **kwargs
    )