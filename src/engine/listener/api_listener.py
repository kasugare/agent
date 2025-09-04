#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.util_common import gen_req_id
from common.util_protocol_parser import parseProtocol
from engine.protocol.protocol_message import genShutdownThread
from engine.listener.request_handler.OnDemandMessageHandler import OnDemandMessageHandler
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from threading import Thread, Lock
import time
import ast

class StasisApiListener:
    def __init__(self, logger, listenerId, netInfo, appMetaPool, routerQ, jobResultQ):
        self._logger = logger
        self._listenerId = listenerId
        self._netInfo = netInfo
        self._appMetaPool = appMetaPool
        self._routerQ = routerQ
        self._jobResultQ = jobResultQ
        self._jobRequestMap = {}

    def _jobResultMsgHandler(self):
        while True:
            try:
                message = self._jobResultQ.get()
                protocol, statCode = parseProtocol(message)

                if protocol == 'SYS_SHUTDOWN':
                    self._logger.warn("Listener Shutdown")
                    break
                elif protocol == 'RES_JOB_RESULT':
                    returnPathList = message.get('returnPathList')
                    returnPath = returnPathList[0]
                    reqId = returnPath.get('reqId')
                    jobOrderMap = self._jobRequestMap.pop(reqId)
                    if not jobOrderMap: continue
                    jobResult = message.get('result')
                    statTS = jobOrderMap['startTS']
                    socketObj = jobOrderMap['socketObj']
                    socketObj.sendall(str(jobResult).encode("utf-8"))
                    socketObj.close()
                elif protocol == "RES_JOB_INFO":
                    returnPathList = message.get('returnPathList')
                    returnPath = returnPathList[0]
                    reqId = returnPath.get('reqId')
                    jobOrderMap = self._jobRequestMap.pop(reqId)
                    if not jobOrderMap: continue
                    jobResult = message.get('result')
                    statTS = jobOrderMap['startTS']
                    socketObj = jobOrderMap['socketObj']
                    socketObj.sendall(str(jobResult).encode("utf-8"))
                    socketObj.close()
            except Exception as e:
                self._logger.exception(e)

    def _runRequest(self, socketObj, message, jobRequestMap):
        try:
            if message.find("null"):
                message = message.replace('null', 'None')
            message = ast.literal_eval(message)
            self._logger.debug(message)
        except SyntaxError as e:
            self._logger.warn("input message error: %s" %(str(message)))
        except Exception as e:
            self._logger.exception(e)
            return

        try:
            self._logger.info(f"- REQ: {message}")
            jobReqType = message.get('jobReqType').upper()

            message['listenerId'] = self._listenerId
            message['reqId'] = gen_req_id()

            if jobReqType == 'REALTIME':
                appCode = message.get('appCode')
                appMeta = self._appMetaPool.get(appCode)
                if not appMeta:
                    self._logger.warn("Not assigned AppCode in app_meta.conf: %s" %(str(appCode)))
                    socketObj.close()
                else:
                    # RealtimeMessageHandler(self._logger, self._routerQ, socketObj, self._jobReqweustMap).processRequest(message)
                    pass
            elif jobReqType == 'ONDEMAND':
                appCode = message.get('appCode')
                appMeta = self._appMetaPool.get(appCode)
                if not appMeta:
                    self._logger.warn("Not assigned AppCode in app_meta.conf: %s" % (str(appCode)))
                    socketObj.close()
                else:
                    OnDemandMessageHandler(self._logger, self._routerQ, socketObj, self._jobReqweustMap).processRequest(message)

            elif jobReqType == 'API':
                pass

            elif jobReqType == 'SYSTEM':
                pass

            else:
                self._logger.warn("Not allowed data: %s" %(str(message)))
                socketObj.close()
        except Exception as e:
            self._logger.exception(e)


    def _runStasisApi(self):
        svrsock = socket(AF_INET, SOCK_STREAM)
        svrsock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        svrsock.bind(self._netInfo['hostInfo'])
        svrsock.listen(self._netInfo['connPool'])

        self._logger.info("# Stasis Api Server ready: %s" %str(self._netInfo))
        self._logger.debug(" - API Listener: %s", str(self._netInfo['hostInfo']))

        while True:
            try:
                socketObj, addr = svrsock.accept()
                self._logger.info("- connected resource provider, adr: %s, port: %d" %(addr[0], addr[1]))

                message = socketObj.recv(self._netInfo['buffSize'])
                message = message.decode('utf-8').replace('\n', '')
                self._logger.info("# [WebSocket] [%s] received message: %s" %(self._listenerId, message))

                clientRequestThread = Thread(target=self._runRequest, args=(socketObj, message, self._jobrequestMap))
                clientRequestThread.setDaemon(True)
                clientRequestThread.start()

            except KeyboardInterrupt as e:
                break
            except UnicodeDecodeError as e:
                self._logger.warn("- Wrong input message: 'utf-8' codec can't decode, invalid start byte")
            except Exception as e:
                self._logger.exception(e)

    def doProcess(self):
        resultHandler = Thread(target=self._jobResultMsgHandler, args=())
        try:
            resultHandler.setDaemon(True)
            resultHandler.start()
            self._runStasisApi()
        except OSError as e:
            self._logger.warn("Address already in use: %d" %(str(self._netInfo['hostInfo'])))
            if resultHandler.is_alive():
                shutdownMsg=  genShutdownThread()
                self._jobResultQ.put_nowait(shutdownMsg)



