#!/usr/bin/env python
# -*- code utf-8 -*-

from http import HTTPStatus
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse
from error.error_pool import DuplicateElementException, DuplicateFieldException, ExpiredTokenException, InUseException, NotDefinedMetaException
from error.parent_exception import *


class ExceptionResponse(JSONResponse):
    def __init__(self, content, status_code: int = 200) -> None:
        super().__init__(
            content,
            status_code,
            headers={"Access-Control-Allow-Origin": "*"}
        )


async def unknown_exception_handler(request: Request, e: Exception):
    content = {
        'status_code': HTTPStatus.INTERNAL_SERVER_ERROR,
        'message': "Unknown Exception",
        'result': {}
    }
    response = ExceptionResponse(
        content=content,
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR
    )
    return response


async def validation_exception_handler(request, exc: RequestValidationError):
    req_validation_typ = exc.errors()[0]['type']

    # 특정 필드가 없는 경우
    if req_validation_typ == "missing":
        detail = "missing_required_field"
    # 필드의 제한 길이를 초과 하는 경우
    elif req_validation_typ == "string_too_long":
        detail = "over_length"
    # 허용 되지 않은 값이 온 경우
    elif req_validation_typ == "literal_error":
        detail = "literal_error"
    else:
        detail = "unknown_reason"

    content = {
        'status_code': 400,
        'message': "Invalid request",
        'result': {
            'err_detail': detail
        }
    }
    response = ExceptionResponse(
        content=content,
        status_code=HTTPStatus.BAD_REQUEST
    )
    return response


async def internal_server_exception_handler(request, exc: InternalServerException):
    content = {
        'status_code': 500,
        'message': "Internal server error",
        'result': {}
    }

    response = ExceptionResponse(
        content=content,
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR
    )
    return response


# Custom Exception Handlers
async def authenticate_exception_handler(request: Request, e: AuthenticateException):
    content = {
        'status_code': 401,
        'message': 'Authentication failed',
        'result': {
            'err_detail': e.err_detail
        }
    }

    response = ExceptionResponse(
        content=content,
        status_code=HTTPStatus.UNAUTHORIZED
    )
    return response


async def duplicate_element_exception_handler(request: Request, e: DuplicateElementException):
    content = {
        'status_code': 409,
        'message': 'Duplicate element',
        'result': {
            'err_detail': e.err_detail
        }
    }

    response = ExceptionResponse(content=content)
    return response


async def duplicate_field_exception_handler(request: Request, e: DuplicateFieldException):
    content = {
        'status_code': 409,
        'message': 'Duplicate field',
        'result': {
            'err_detail': e.err_detail
        }
    }

    response = ExceptionResponse(content=content)
    return response


async def expired_token_exception_handler(request: Request, e: ExpiredTokenException):
    content = {
        'status_code': 419,
        'message': 'Expired token',
        'result': {
            'err_detail': e.err_detail
        }
    }

    response = ExceptionResponse(
        content=content,
        status_code=HTTPStatus.UNAUTHORIZED
    )
    return response


async def inuse_exception_handler(request: Request, e: InUseException):
    content = {
        'status_code': 422,
        'message': 'Data in use',
        'result': {
            'err_detail': e.err_detail
        }
    }

    response = ExceptionResponse(
        content=content,
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR
    )
    return response


async def invalid_input_exception_handler(request: Request, e: InvalidInputException):
    content = {
        'status_code': 400,
        'message': 'Invalid input',
        'result': {
            'err_detail': e.err_detail
        }
    }

    response = ExceptionResponse(
        content=content,
        status_code=HTTPStatus.BAD_REQUEST
    )
    return response


async def not_found_exception_handler(request: Request, e: NotFoundException):
    content = {
        'status_code': 404,
        'message': 'Content not found',
        'result': {
            'err_detail': e.err_detail
        }
    }

    response = ExceptionResponse(
        content=content,
        status_code=HTTPStatus.NOT_FOUND
    )
    return response


async def token_exception_handler(request: Request, e: TokenException):
    content = {
        'status_code': 401,
        'message': 'Token error',
        'result': {
            'err_detail': e.err_detail
        }
    }

    response = ExceptionResponse(
        content=content,
        status_code=HTTPStatus.UNAUTHORIZED
    )
    return response


async def authorization_exception_handler(request: Request, e: AuthorizationException):
    content = {
        'status_code': 403,
        'message': 'Authorization failed',
        'result': {
            'err_detail': e.err_detail
        }
    }

    response = ExceptionResponse(
        content=content,
        status_code=HTTPStatus.UNAUTHORIZED
    )
    return response


async def not_acceptable_exception_handler(request: Request, e: NotAcceptableException):
    content = {
        'status_code': 406,
        'message': 'Not Acceptable',
        'result': {
            'err_detail': e.err_detail
        }
    }

    response = ExceptionResponse(
        content=content,
        status_code=HTTPStatus.NOT_FOUND
    )
    return response

async def not_defined_workflow_meta_exception_handler(request: Request, e: NotDefinedMetaException):
    content = {
        'status_code': 405,
        'message': 'Workflow load failed',
        'result': {
            'err_detail': e.err_detail
        }
    }

    response = ExceptionResponse(
        content=content,
        status_code=HTTPStatus.NOT_FOUND
    )
    return response


def register_exception_handlers(app: FastAPI):
    app.add_exception_handler(Exception, unknown_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    app.add_exception_handler(AuthenticateException, authenticate_exception_handler)
    app.add_exception_handler(DuplicateElementException, duplicate_element_exception_handler)
    app.add_exception_handler(DuplicateFieldException, duplicate_field_exception_handler)
    app.add_exception_handler(NotFoundException, not_found_exception_handler)
    app.add_exception_handler(TokenException, token_exception_handler)
    app.add_exception_handler(AuthorizationException, authorization_exception_handler)
    app.add_exception_handler(InvalidInputException, invalid_input_exception_handler)
    app.add_exception_handler(InternalServerException, internal_server_exception_handler)
    app.add_exception_handler(NotAcceptableException, not_found_exception_handler)
    app.add_exception_handler(NotDefinedMetaException, not_defined_workflow_meta_exception_handler)
