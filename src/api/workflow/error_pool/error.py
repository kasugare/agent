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


class MismatchedRequirementsError(Exception):
    def __init__(self):
        super().__init__("Fail to meet the conditions/requirements")
        self._errorMessage = "Asset information is inconsistent"

    def __str__(self):
        return self._errorMessage


class NotExistRequiredNodesError(Exception):
    def __init__(self):
        super().__init__("not exist required node error")
        self._errorMessage = "not exist required node error"

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
        self._errorCode = "NotDefinedProtocolMessage"
        self._errorMessage = "Not defined protocol message format"

    def __str__(self):
        return self._errorMessage

    def error_code(self):
        return self._errorCode


class InvalidInputException(Exception):
    def __init__(self):
        super().__init__("Invalid input params")
        self._errorCode = "InvalidInputParametersException"
        self._errorMessage = "Invalid input params"

    def __str__(self):
        return self._errorMessage

    def error_code(self):
        return self._errorCode


class NotDefinedWorkflowMetaException(Exception):
    def __init__(self):
        super().__init__("Not defined workflow meta")
        self._errorCode = "NotDefinedWorkflowMetaException"
        self._errorMessage = "Not defined workflow meta"

    def __str__(self):
        return self._errorMessage

    def error_code(self):
        return self._errorCode


class UnauthorizedKeyError(Exception):
    def __init__(self):
        super().__init__("Not authorized key")
        self._errorCode = "UnauthorizedKeyError"
        self._errorMessage = "auth key is not allowed key"

    def __str__(self):
        return self._errorMessage

    def error_code(self):
        return self._errorCode


class ExceedExecutionRetryError(Exception):
    def __init__(self):
        super().__init__("Exceed execution retry")
        self._errorCode = "ExceedExecutionRetryError"
        self._errorMessage = "The task timed out and failed after exceeding the max retry limit."

    def __str__(self):
        return self._errorMessage

    def error_code(self):
        return self._errorCode