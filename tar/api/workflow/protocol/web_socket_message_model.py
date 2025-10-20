#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Annotated, Dict, Optional
from pydantic import BaseModel, Field


class WebSocketMessage(BaseModel):
    type: Annotated[str, Field(max_length=20, description="Type of data", examples=["connect"])]
    payload: Annotated[Dict, Field(description="Payload of websocket protocol")]
    request_id: Annotated[Optional[str], Field(default="", max_length=50, description="request uuid", examples=["3abaae15-ecf1-40ba-9dce-45b452d008f1"])]