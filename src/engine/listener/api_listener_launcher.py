#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.util_logger import Logger
from engine.listener.api_listener import StasisApiListener
from multiprocessing import Process, Queue
from threading import Thread, Lock
import time
import sys

class StasisApiListenerManager:
    def __init__(self, logger, sysContext, qPack):
        self._logger = logger
        self._debugMode = sysContext.get('debugMode')
        self._netInfos = sysContext.get('netInfos')
        self._appMetaPool = sysContext.get('appMeta')
        self._qPack = qPack
        self._jobListenerInfo = {}

    def _genLogger(self):
        listenerLogger = self._logger
        try:
            listenerLogger = Logger(confName="API_LISTENER").getLogger()
            if self._debugMode:
                listenerLogger.setLevel("DEBUG")
            else:
                listenerLogger.setLevel("INFO")
        except Exception as e:
            self._logger.warn("# Can not created listener logger")
        return listenerLogger

    def _setJobListenerInfo(self, listenerId, apiListener, jobResultQ):
        self._jobListenerInfo[listenerId] = {
            'pid': apiListener.pid,
            'jobResultQ': jobResultQ
        }

    def _runJobResultHandler(self, listenerQ, listenerLogger):
        while True:
            try:
                message = listenerQ.get()
                protocol = message.get('protocol')
                listenerLogger.debug(message)

                if protocol == 'RES_JOB_RESULT':
                    returnPathList = message.get('returnPathList')
                    returnPath = returnPathList[0]
                    listenerId = returnPath.get('listenerId')
                    jobResultQ = self._jobListenerInfo[listenerId]['jobResultQ']
                    jobResultQ.put_nowait(message)

                elif protocol == 'RES_JOB_INFO':
                    returnPathList = message.get('returnPathList')
                    returnPath = returnPathList[0]
                    listenerId = returnPath.get('listenerId')
                    jobResultQ = self._jobListenerInfo[listenerId]['jobResultQ']
                    jobResultQ.put_nowait(message)
            except EOFError as e:
                self._logger.warn("System Shutdown")
                break
            except Exception as e:
                listenerLogger.exception(e)

    def _launchListener(self, listenerLogger, listenerId, netInfo, routerQ, jobResultQ):
        StasisApiListener(listenerLogger, listenerId, netInfo, self._appMetaPool, routerQ, jobResultQ).doProcess()

    def doLauncher(self):
        try:
            listenerLogger = self._genLogger()
            listenerQ = self._qPack['listenerQ']
            routerQ = self._qPack['routerQ']

            resultHandler = Thread(target=self._runJobResultHandler, args=(listenerQ, listenerLogger,))
            resultHandler.setDaemon(True)
            resultHandler.start()

            for index in range(len(self._netInfos)):
                time.sleep(0.1)
                jobResultQ = Queue()
                netInfo = self._netInfos[index]
                listenerId = "listener_%d" %(index+1)
                appListener = Process(target=self._launchListener, args=(listenerLogger, listenerId, netInfo, routerQ, jobResultQ))
                appListener.start()
                self._setJobListenerInfo(listenerId, appListener, jobResultQ)
        except Exception as e:
            self._logger.exception(e)
            sys.exit(1)
