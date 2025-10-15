#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.util_datetime import tzHtime
import time


def req_auth_key_protocol() -> dict:
    message = {
        "protocol": "REQ_AUTH_KEY",
        "header": {
            "timestamp": {
                "req_time": "",
                "res_time": ""
            },
            "request_id": "key-001",
            "session_id": "sid-001"
        },
        "payload": {}
    }
    return message


def SYS_AUTH_KEY_MSG(request_id, auth_key):
    message = {
        "protocol": "RES_AUTH_KEY",
        "request_id": request_id,
        "result": {
            "auth_key": auth_key
        }
    }
    return message


def RES_AUTH_KEY(request_id: str, session_id: str, req_time, auth_key: str, error=None) -> dict:
    """
        result = {
            "auth_key": "api-key-001"
        }
    """
    if not error:
        msg_state = "success"
    else:
        msg_state = "error"

    message = {
        "protocol": "RES_AUTH_KEY",
        "header": {
            "timestamp": {
                "req_time": req_time,
                "res_time": tzHtime(time.time()*1000)
            },
            "request_id": request_id,
            "session_id": session_id
        },
        "payload": {
            "status_code": 200,
            "message": msg_state,
            "result": {
                "auth_key": auth_key
            }
        }
    }
    return message

def req_run_query() -> dict:
    message = {
        "protocol": "REQ_CHAT_QUERY",
        "header": {
            "timestamp": {
                "req_time": "",
                "res_time": ""
            },
            "request_id": "chat-001",
            "session_id": "sid-001",
            "auth_key": "key-001"
        },
        "payload": {
            "question": "blablabla..."
        }
    }
    return message


def SYS_WF_RESULT_MSG(request_id, answer) -> dict:
    message = {
        "protocol": "RES_CHAT_QUERY",
        "request_id": request_id,
        "result": {
            "answer": answer
        }
    }
    return message


def RES_WF_RESULT(request_id: str, session_id: str, req_time: str, result: dict, error=None) -> dict:
    """
        result = {
            "answer": "blablabla..."
        }
    """

    if not error:
        msg_state = "success"
    else:
        msg_state = "error"

    message = {
        "protocol": "RES_CHAT_QUERY",
        "header": {
            "timestamp": {
                "req_time": req_time,
                "res_time": tzHtime(time.time()*1000)
            },
            "request_id": request_id,
            "session_id": session_id
        },
        "payload": {
            "status_code": 200,
            "message": msg_state,
            "result": result
        }
    }
    return message


def req_nodes_state() -> dict:
    message = {
        "protocol": "REQ_NODES_STATUS",
        "header": {
            "timestamp": {
                "req_time": "",
                "res_time": ""
            },
            "request_id": "ndsts-001",
            "session_id": "sid-001",
            "auth_key": "key-001"
        },
        "payload": {
            "node_ids": ["nd-001"]
        }
    }
    return message


def SYS_NODE_STATUS(request_id, node_id, service_name, status, timestamp) -> dict:
    message = {
        "protocol": "RES_NODE_STATUS",
        "request_id": request_id,
        "result": {
            "node_id": node_id,
            "service_name": service_name,
            "status": status,
            "timestamp": timestamp
        }
    }
    return message


def RES_NODE_STATUS(request_id: str, session_id: str, req_time: str, node_status: dict, error=None) -> dict:
    """
        nodes_status = [
            {
                "node_id": "nd-001",
                "data": "STATUS: RUNNING/PENDING/....",
                "timestamp": ""
            }
        ]
    """
    if not error:
        msg_state = "success"
    else:
        msg_state = "error"

    message = {
        "protocol": "RES_NODE_STATUS",
        "header": {
            "timestamp": {
                "req_time": req_time,
                "res_time": tzHtime(time.time()*1000)
            },
            "request_id": request_id,
            "session_id": session_id
        },
        "payload": {
            "status_code": 200,
            "message": msg_state,
            "result": node_status
        }
    }
    return message

def RES_NOT_ALLOWED_MSG(error_msg, user_message):
    message = {
        "protocol": "RES_NOT_ALLOWED_MESSAGE",
        "header": {
            "timestamp": {
                "res_time": tzHtime(time.time() * 1000)
            }
        },
        "payload": {
            "status_code": 400,
            "message": "error",
            "error_msg": error_msg,
            "input_msg": user_message
        }
    }
    return message