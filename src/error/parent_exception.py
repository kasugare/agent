#!/usr/bin/env python
# -*- code utf-8 -*-

class AuthenticateException(Exception):
    def __init__(self, err_msg=None, err_detail=None):
        if err_msg:
            self.err_msg = err_msg
        else:
            self.err_msg = self.__class__.__name__
        self.err_detail = err_detail
        super().__init__(self.err_msg)


class DuplicateException(Exception):
    def __init__(self, err_msg=None, err_detail=None):
        if err_msg:
            self.err_msg = err_msg
        else:
            self.err_msg = self.__class__.__name__
        self.err_detail = err_detail
        super().__init__(self.err_msg)


class InternalServerException(Exception):
    def __init__(self, err_msg=None, err_detail=None):
        if err_msg:
            self.err_msg = err_msg
        else:
            self.err_msg = self.__class__.__name__
        self.err_detail = err_detail
        super().__init__(self.err_msg)


class NotFoundException(Exception):
    def __init__(self, err_msg=None, err_detail=None):
        if err_msg:
            self.err_msg = err_msg
        else:
            self.err_msg = self.__class__.__name__
        self.err_detail = err_detail
        super().__init__(self.err_msg)


class TokenException(Exception):
    def __init__(self, err_msg=None, err_detail=None):
        if err_msg:
            self.err_msg = err_msg
        else:
            self.err_msg = self.__class__.__name__
        self.err_detail = err_detail
        super().__init__(self.err_msg)


class InvalidInputException(Exception):
    def __init__(self, err_msg=None, err_detail=None):
        if err_msg:
            self.err_msg = err_msg
        else:
            self.err_msg = self.__class__.__name__
        self.err_detail = err_detail
        super().__init__(self.err_msg)


class AuthorizationException(Exception):
    def __init__(self, err_msg=None, err_detail=None):
        if err_msg:
            self.err_msg = err_msg
        else:
            self.err_msg = self.__class__.__name__
        self.err_detail = err_detail
        super().__init__(self.err_msg)


class NotAcceptableException(Exception):
    def __init__(self, err_msg=None, err_detail=None):
        if err_msg:
            self.err_msg = err_msg
        else:
            self.err_msg = self.__class__.__name__
        self.err_detail = err_detail
        super().__init__(self.err_msg)


class DeleteException(Exception):
    def __init__(self, err_msg=None, err_detail=None):
        if err_msg:
            self.err_msg = err_msg
        else:
            self.err_msg = self.__class__.__name__
        self.err_detail = err_detail
        super().__init__(self.err_msg)


class NotDefinedMetaException(Exception):
    def __init__(self, err_msg=None, err_detail=None):
        if err_msg:
            self.err_msg = err_msg
        else:
            self.err_msg = self.__class__.__name__
        self.err_detail = err_detail
        super().__init__(self.err_msg)