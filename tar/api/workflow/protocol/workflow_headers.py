#!/usr/bin/env python
# -*- code utf-8 -*-

from typing import Annotated, Dict, Optional, Any
from pydantic import BaseModel, Field
from fastapi import Header


class HeaderModel(BaseModel):
    request_id: str
    session_id: str



async def get_headers(
        request_id: Annotated[str, Header(..., alias="request_id")],
        session_id: Annotated[str, Header(..., alias="session_id")]
) -> HeaderModel:
    return HeaderModel(request_id=request_id, session_id=session_id)
