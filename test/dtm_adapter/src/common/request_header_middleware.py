#!/usr/bin/env python
# -*- code utf-8 -*-

import os
import secrets
from contextvars import ContextVar
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED

from ailand.common.logger import Logger
from common.conf_system import getSecretKey

_logger = Logger()

# Secret Key 환경 변수 로드 및 부재 시 애플리케이션 중단
# SECRET_KEY = os.getenv("SECRET_KEY")
SECRET_KEY = getSecretKey()
if not SECRET_KEY:
    raise ValueError("SECRET_KEY 환경 변수가 설정되지 않았습니다.")

# Context 정의
current_session_id: ContextVar[Optional[str]] = ContextVar("session_id", default=None)
current_usr_id: ContextVar[Optional[str]] = ContextVar("usr_id", default=None)


class WfEngineReqHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Secret-Key 인증
        secret_key_header = request.headers.get("secret_key")

        print("secret_key_header: ", secret_key_header)
        print("SECRET_KEY: ", SECRET_KEY)
        if not secret_key_header or not secrets.compare_digest(secret_key_header, SECRET_KEY):

            _logger.warning("Authentication failed: Invalid or missing Secret-Key.")
            auth_error_response = JSONResponse(
                status_code=HTTP_401_UNAUTHORIZED,
                content={"message": "Authentication Error", "result": {"err_detail": "Invalid or missing Secret-Key"}}
            )
            return auth_error_response

        # 필수 헤더(Session-ID, User-ID) 검증
        session_id = request.headers.get("session_id")
        usr_id = request.headers.get("user_id")
        print("session_id: ", session_id)
        print("usr_id: ", usr_id)

        if not session_id or not usr_id:
            _logger.warning("Bad Request: Missing Session-ID or User-ID header.")
            bad_request_response = JSONResponse(
                status_code=HTTP_400_BAD_REQUEST,
                content={"message": "Bad Request", "result": {"err_detail": "Session-ID and User-ID headers are required."}}
            )
            return bad_request_response

        _logger.info("Valid headers. Save header values to context.")
        current_session_id.set(session_id)
        current_usr_id.set(usr_id)

        response = await call_next(request)
        return response