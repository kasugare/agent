#!/usr/bin/env python
# -*- coding: utf-8 -*-

class NotPreparedPrevJob(Exception):
    def __init__(self):
        super().__init__("Task not done")
        self._errorMessage = "task not done"

    def __str__(self):
        return self._errorMessage


class NotExistedData(Exception):
    def __init__(self):
        super().__init__("Not existed data in data pool")
        self._errorMessage = "Not existed data in data pool"

    def __str__(self):
        return self._errorMessage


class AssetKeyError(Exception):
    def __init__(self):
        super().__init__("Asset's keys mismatch detected between dictionaries")
        self._errorMessage = "Asset's keys mismatch detected between dictionaries"

    def __str__(self):
        return self._errorMessage


class EnvironmentKeyError(Exception):
    def __init__(self):
        super().__init__("Environment's keys mismatch detected between dictionaries")
        self._errorMessage = "Environment's keys mismatch detected between dictionaries"

    def __str__(self):
        return self._errorMessage


class NotDefinedProtocolMessage(Exception):
    def __init__(self):
        super().__init__("Not defined protocol message format")
        self._errorMessage = "Not defined protocol message format"

    def __str__(self):
        return self._errorMessage