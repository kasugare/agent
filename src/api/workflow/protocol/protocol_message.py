#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Annotated, Dict, Optional
from pydantic import BaseModel, Field
import time


def gen_task_order(task_id: str, service_id: str, edge_id: str, api_url_info, edge_info) -> dict:
    if not task_id:
        task_id = "%X" %(int(time.time() * 1000000))
    message = {
        'protocol': 'REQ_TASK_RUN',
        'task_id': task_id,
        'service_id': service_id,
        'orders': {
            'endpoint': api_url_info,
            'task_meta': {
                'edge_id': edge_id,
                'edge_info': edge_info
            }
        }
    }
    return message


class WebSocketMessage(BaseModel):
    type: Annotated[str, Field(max_length=20, description="Type of data", examples=["connect"])]
    payload: Annotated[Dict, Field(description="Payload of websocket protocol")]
    request_id: Annotated[Optional[str], Field(default="", max_length=50, description="request uuid", examples=["3abaae15-ecf1-40ba-9dce-45b452d008f1"])]