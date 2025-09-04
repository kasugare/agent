#!/usr/bin/env python
# -*- coding: utf-8 -*-

from engine.protocol.protocol_message import genReqJobInfo, genResetScheduler, genStopJob
from engine.listener.request_handler.RequestHandler import RequestHandler

class SystemControlMessageHandler(RequestHandler):
    def __init__(self, logger, routerQ, socketObj, jobRequestMap):
        RequestHandler.__init__(self, logger, routerQ, socketObj, jobRequestMap)
        self._logger = logger
        self._routerQ = routerQ

    def _resetJobSchedule(self, listenerId, reqId):
        returnPath = {'listenerId': listenerId, 'reqId': reqId}
        jobMessage = genResetScheduler(returnPath)
        self._routherQ.put_nowait(jobMessage)

    def _getJobInfo(self, listenerId, reqId):
        returnPath = {'listenerId': listenerId, 'reqId': reqId}
        jobMessage = genReqJobInfo(listenerId, reqId)
        self._routerQ.put_nowait(jobMessage)

    def _getJobStatus(self, jobId):
        jobMessage = genResetScheduler()
        self.f_routerQ.put_nowait(jobMessage)

    def _stopJobExecutoer(self, params):
        jobId = params.get('jobID')
        executorId = params.get('executorId')
        jobMessage = genStopJob(jobId, executorId)
        self._routerQ.put_nowait(jobMessage)


    def processRequest(self, message):
        listenerId, reqId, jobReqType, jobOrder, appCode, isReturn, params = self.parseMessage(message)

        if jobOrder == 'RESET_SCHEDULER':
            self._resetJobSchedule(listenerId, reqId)

        elif jobOrder == 'GET_JOB_INFO':
            self._getJobInfo(listenerId, reqId)

        elif jobOrder == 'GET_JOB_RESOURCE_INFO':
            self._getJobInfo(listenerId, reqId)

        elif jobOrder == 'REQ_JOB_STATUS':
            self._getJobStatus(reqId)

        elif jobOrder == 'REQ_STOP_JOB':
            self._stopJobExecutoer(params)

        else:
            self._logger.warn("# Wrong Protocol: %s" %(str(message)))
            self.closeSocket()