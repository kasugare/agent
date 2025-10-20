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


def RES_AUTH_KEY(request_id: str, session_id: str, req_time, result: str) -> dict:
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
            "message": "success",
            "result": [result]
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
            "params": {
                "question": "blablabla..."
            }
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
            "result": [result]
        }
    }
    return message



def SYS_NODE_STATUS(request_id, node_id, service_name, status, timestamp) -> dict:
    message = {
        "protocol": "RES_NODE_STATUS",
        "request_id": request_id,
        "result": [
            {
                "node_id": node_id,
                "service_name": service_name,
                "status": status,
                "timestamp": timestamp
            }
        ]
    }
    return message


def RES_NODES_STATUS(request_id: str, session_id: str, req_time: str, nodes_status: dict) -> dict:
    """
        nodes_status = [
            {
                "node_id": "nd-001",
                "service_name": "{node`s service_name}",
                "status": "PENDING/SCHEDULED/QUEUE/RUNNING/COMPLETED/FAILED/PAUSED/STOPED/SKIPPED/BLOCKED",
                "timestamp": ""
            }
        ]
    """
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
            "message": "success",
            "result": nodes_status
        }
    }
    return message


def RES_EMPTY_META_MSG(error_code, error_msg):
    message = {
        "protocol": "RES_EMPTY_META",
        "header": {
            "timestamp": {
                "res_time": tzHtime(time.time() * 1000)
            }
        },
        "payload": {
            "status_code": 405,
            "message": "error",
            "error": [
                {
                    "error_code": error_code,
                    "error_message": error_msg
                }
            ]
        }
    }
    return message


def RES_INVALID_PARAMS_MSG(error_code, error_msg):
    message = {
        "protocol": "RES_INVALID_PARAMS",
        "header": {
            "timestamp": {
                "res_time": tzHtime(time.time() * 1000)
            }
        },
        "payload": {
            "status_code": 400,
            "message": "error",
            "error": [
                {
                    "error_code": error_code,
                    "error_message": error_msg
                }
            ]
        }
    }
    return message


def RES_UNAUTHRIZED_MSG(error_code, error_msg):
    message = {
        "protocol": "RES_UNAUTH",
        "header": {
            "timestamp": {
                "res_time": tzHtime(time.time() * 1000)
            }
        },
        "payload": {
            "status_code": 401,
            "message": "error",
            "error": [
                {
                    "error_code": error_code,
                    "error_message": error_msg
                }
            ]
        }
    }
    return message

def RES_NOT_ALLOWED_MSG(error_code, error_msg):
    message = {
        "protocol": "RES_NOT_ALLOWED_MESSAGE",
        "header": {
            "timestamp": {
                "res_time": tzHtime(time.time() * 1000)
            }
        },
        "payload": {
            "status_code": 406,
            "message": "error",
            "error": [
                {
                    "error_code": error_code,
                    "error_message": error_msg
                }
            ]
        }
    }
    return message
