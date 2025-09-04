#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

class RequestHandler:
    def __init__(self, logger, routerQ, socketObj, jobRequestMap):
        self._logger = logger
        self._routerQ = routerQ
        self._socketObj = socketObj
        self._jobRequestMap = jobRequestMap

    def closeSocket(self):
        if self._socketObj:
            self._socketObj.close()

    def parseMessage(self, message):
        listenerId = message.get('listenerId')
        reqId = message.get('reqId')
        jobReqType = str(message.get("jobReqType")).upper()
        jobOrder = str(message.get('jobOrder')).upper()
        appCode = message.get('appCode')
        isReturn = message.get('isReturn')
        params = message.get('params')

        if isinstance(isReturn, bool):
            isReturn = str(isReturn)

        if isReturn.lower() == 'true':
            isReturn = True
            message['isReturn'] = True

            self._jobRequestMap[reqId] = {
                'socketObj': self._socketObj,
                'startTs': time.time(),
                'message': message
            }
        else:
            isReturn = False
            message['isReturn'] = False
            self._socketOjb.close()

        return listenerId, reqId, jobReqType, jobOrder, appCode, isReturn, params