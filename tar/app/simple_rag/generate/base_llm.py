#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from typing import Dict, Generator


class BaseLLM(ABC):
    def __init__(self, logger):
        self._logger = logger

    @abstractmethod
    def generate(self, prompt: str, stream: bool = False) -> Dict:
        pass

    def stream_generate(self, prompt: str) -> Generator[str, None, None]:
        raise NotImplementedError("Streaming not implemented for this LLM.")
