#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ast import literal_eval
from api.workflow.error_pool.error import NotDefinedProtocolMessage


class ProtocolParser:
    def __init__(self, logger):
        self._logger = logger

    def message_to_dict(self, message):
        try:
            if isinstance(message, str):
                message = literal_eval(message)
                return message
            elif isinstance(message, dict):
                return message
            else:
                raise NotDefinedProtocolMessage
        except Exception as e:
            raise NotDefinedProtocolMessage

    def parse_system_protocl(self, message):
        if not isinstance(message, dict) or not message.get('protocol'):
            raise NotDefinedProtocolMessage
        protocol = message.get('protocol')
        request_id = message.get('request_id')
        result = message.get('result')
        return protocol, request_id, result

    def parse_client_protocol(self, message):
        if not isinstance(message, dict) or not message.get('protocol'):
            raise NotDefinedProtocolMessage

        protocol = message.get('protocol')
        message_header = message.get('header')
        if not message_header:
            raise NotDefinedProtocolMessage

        request_id = message_header.get('request_id')
        return protocol, request_id