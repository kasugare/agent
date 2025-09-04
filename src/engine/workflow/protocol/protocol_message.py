#!/usr/bin/env python
# -*- coding: utf-8 -*-

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