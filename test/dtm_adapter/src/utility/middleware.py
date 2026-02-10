from ailand.common.logger import Logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

_logger = Logger()


class CSPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = "default-src *; img-src *; script-src * 'unsafe-inline'; style-src * 'unsafe-inline';"
        return response
