#!/usr/bin/env python
# -*- coding: utf-8 -*-


def parseProtocol(message):
	if not message or 'protocol' not in message.keys():
		raise ValueError
	protocol = message['protocol']
	statCode = message['statCode']
	return protocol, statCode

def parseClientProtocol(message):
	if not message or 'protocol' not in message.keys() or 'clientId' not in message.keys():
		raise ValueError
	protocol = message.et('protocol')
	statCode = message.et('statCode')
	clientId = message.et('clientId')
	return protocol, statCode, clientId

