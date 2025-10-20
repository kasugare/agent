#!/usr/bin/env python
# -*- code utf-8 -*-

from typing import Annotated, Dict, Optional, Any
from pydantic import BaseModel, Field


class ReqCreateWorkflow(BaseModel):
    meta: Annotated[Dict[str, Any], Field(description="meta")]


class ResCreateWorkflow(BaseModel):
    pass


class ReqCallDataClear(BaseModel):
    pass


class ResCallDataClear(BaseModel):
    pass


class ReqCallChainedModelService(BaseModel):
    from_node: Optional[Annotated[str | None, Field(description='from')]] = None
    to_node: Optional[Annotated[str | None, Field(description='to')]] = None
    parameter: Annotated[Dict[str, Any], Field(description='')]


class ResCallChainedModelService(BaseModel):
    answer: Annotated[Dict[str, Any] | None, Field(description='answer')] = None


class ReqCallDataPool(BaseModel):
    node_id: Annotated[str, Field(description='노드 ID')]


class ResCallDataPool(BaseModel):
    node_id: Annotated[str, Field(description='노드 ID')]
    data: Annotated[Dict[str, Any], Field(description='노드 상태 데이터')]
    timestamp: Annotated[str, Field(description='timestamp')]


class WebSocketMessage(BaseModel):
    type: Annotated[str, Field(max_length=20, description="Type of data", examples=["connect"])]
    payload: Annotated[Dict, Field(description="Payload of websocket protocol")]
    request_id: Annotated[Optional[str], Field(default="", max_length=50, description="request uuid",
                                               examples=["3abaae15-ecf1-40ba-9dce-45b452d008f1"])]
