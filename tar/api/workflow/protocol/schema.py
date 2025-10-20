#!/usr/bin/env python
# -*- code utf-8 -*-

from typing import TypeVar, Generic

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field


T = TypeVar('T')


class BaseResponse(BaseModel, Generic[T]):
    status_code: int = Field(200, description="상태 코드")
    message: str = Field('success', max_length=200, description="부가 설명")
    result: T | None = Field(default=None)

    def __init__(self, status_code=200, message='success', result=None):
        super().__init__(
            status_code=status_code,
            message=message,
            result=result
        )

    def to_dict(self):
        return jsonable_encoder(self)
