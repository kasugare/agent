#!/usr/bin/env python
# -*- code utf-8 -*-

from typing import Annotated

from pydantic import BaseModel, Field


class ReqModelOfGreet(BaseModel):
    name: Annotated[str, Field(max_length=30, description="이름", examples=["Tommy"])]


class ResModelOfGreet(BaseModel):
    greeting: Annotated[str, Field(description="인사말", examples=["Hello world, Tommy!"])]
