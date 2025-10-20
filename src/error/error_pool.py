#!/usr/bin/env python
# -*- code utf-8 -*-

from error.parent_exception import *


class DuplicateElementException(DuplicateException):
    pass


class DuplicateFieldException(DuplicateException):
    pass


class ExpiredTokenException(TokenException):
    def __init__(self, err_msg=None, err_detail="expired"):
        super().__init__(err_msg, err_detail)


class MissingFieldDataException(InternalServerException):
    pass


class InvalidUserException(AuthenticateException):
    def __init__(self, err_msg=None, err_detail="invalid_user_id"):
        super().__init__(err_msg, err_detail)


class InactiveUserException(AuthenticateException):
    def __init__(self, err_msg=None, err_detail="inactive_user"):
        super().__init__(err_msg, err_detail)


class SecureLockException(AuthenticateException):
    def __init__(self, err_msg=None, err_detail="secure_locked_user"):
        super().__init__(err_msg, err_detail)


class InvalidPayloadTokenException(TokenException):
    def __init__(self, err_msg=None, err_detail="invalid_payload"):
        super().__init__(err_msg, err_detail)


class InvalidSignatureTokenException(TokenException):
    def __init__(self, err_msg=None, err_detail="invalid_signature"):
        super().__init__(err_msg, err_detail)


class EmptyInputException(InvalidInputException):
    def __init__(self, err_msg=None, err_detail="empty_input"):
        super().__init__(err_msg, err_detail)


class InUseException(InternalServerException):
    pass
