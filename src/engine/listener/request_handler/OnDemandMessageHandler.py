#!/usr/bin/env python
# -*- coding: utf-8 -*-

from engine.protocol.protocol_message import genJobContext, genOndemandJobOrder
from engine.listener.request_handler.RequestHandler import RequestHandler

class OnDemandMessageHandler(RequestHandler):
    def __init__(self, logger, routerQ, socketObj, jobRequestMap):
        RequestHandler.__init__(self, logger, routerQ, socketObj, jobRequestMap)
        self._logger = logger
        self._routerQ = routerQ
        self._socketObj = socketObj

    def _orderStart(self, listenerId, reqId, jobReqType, jobOrder, appCode, isReturn, params):
        jobContext = genJobContext(jobOrder, appCode, isReturn, params)
        returnPath = {'listenerId': listenerId, 'reqId': reqId}
        jobMessage = genOndemandJobOrder(jobReqType=jobReqType, jobContext=jobContext, returnPath=returnPath, isReturn=isReturn)
        self._routerQ.put_nowait(jobMessage)

    def _orderStop(self, jobId):
        # self._routerQ.put_nowait(jobMessage)
        pass

    def _orderStatue(self, jobId):
        # self._routerQ.put_nowait(jobMessage)
        pass

    def _reqOrder(self, listenerId, reqId, jobReqType, jobOrder, appCode, isReturn, params):
        jobContext = genJobContext(jobOrder, appCode, isReturn, params)
        returnPath = {'listenerId': listenerId, 'reqId': reqId}
        jobMessage = genOndemandJobOrder(jobReqType=jobReqType, jobContext=jobContext, returnPath=returnPath, isReturn=isReturn)
        self._routerQ.put_nowait(jobMessage)

    def processRequest(self, message):
        listenerId, reqId, jobReqType, jobOrder, appCode, isReturn, params = self.parseMessage(message)

        if jobOrder == 'START':
            self._orderStart(listenerId, reqId, jobReqType, jobOrder, appCode, isReturn, params)
        # elif jobOrder == 'STOP':
        #     self._orderStop(jobId)
        # elif jobOrder == 'STATUS':
        #     self._orderStatus(jobId)
        else:
            self._logger.warn("# Wrong Protocol: %s" %(str(message)))
            self.closeSocket()