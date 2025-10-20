#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Output:
    def __init__(self, type: str, prompt: str):
        self._type = type
        self._prompt = prompt

    def set_output(self, answer: str):
        output = {
            "output": answer
        }
        return output

