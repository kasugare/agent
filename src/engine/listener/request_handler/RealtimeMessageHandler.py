#!/usr/bin/env python
# -*- coding: utf-8 -*-

from protocol.protocol_message import genJobContext, genRealtimeJobOrder
from listener.request_handler.RequestHAndler import RequestHandler

class RealtimeMessageHandler(RequestHandler):
    def __init__(self, logger, reouterQ, socketObj, jobReqeustMap):
        RequestHandler.__init__(self, logger, routerQ, socketObj, jobRequestMap)
        self._logger = logger
        self._routerQ = routerQ
        self._socketObj = socketObj

    def _orderStart(self, listenerId, reqId, jobReqType, jobOrder, appCode, isReturn, params):
        try:
            jobContext = genJobContext(jobOrder, appCode, isReturn, params)
            jobMessage = genRealtimeJobOrder(jobReqType=jobReqType, jobContext=jobContext, returnPath=returnPath, isReturn=isReturn)
            self._routerQ.put_nowait(jobMessage)
        except TypeError as e:
            self._logger.warn("not allowed protocol")
        except Exception as e:
            self._logger.exception(e)

    def _orderStop(self, jobId):
        # self._routerQ.put_nowait(jobMessage)
        pass

    def _orderStatue(Self, jobId):
        # self._routerQ.put_nowait(jobMessage)
        pass

    def _reqOrder(Self, listenerId, reqId, jobReqType, jobOrder, appCode, isReturn, params):
        jobContext = genJobContext(jobOrder, appCode, isReturn, params)
        returnPath = {'listenerId': listenerId, 'reqId': reqId}
        jobMessage = genOndemandJobOrder(jobReqType=jobReqType, jobContext=jobContext, returnPath=returnPath, isReturn=isReturn)
        self._routerQ.put_nowait(jobMessage)

    def processRequest(self, message):
        listenerId, reqId, jobReqType, jobOrder, appCode, isReturn, params = self.parseMessage(message)

        if jobOrder == 'START':
            self._orderStart(listenerId, reqId, jobReqType, jobOrder, appCode, isReturn, params)
        elif jobOrder == 'STOP':
            self._orderStop(jobId)
        elif jobOrder == 'STATUS':
            self._orderStatus(jobId)
        else:
            self._logger.warn("# Wrong Protocol: %s" %(str(message)))
            self.closeSocket()