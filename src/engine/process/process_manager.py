#!/usr/bin/env python
# -*- coding: utf-8 -*-

from engine.process.process_launcher import ProcessLauncher
from multiprocessing import Queue
import multiprocessing as mp
import sys

class ProcessManager:
    def __init__(self, logger, sysContext):
        self._logger = logger
        self._sysContext = sysContext
        # mp.freeze_support()
        # mp.set_start_method('fork')

    def _gen_queue_pack(self):
        q_pack = {
            'systemQ': Queue(),
            'routerQ': Queue(),
            'scheMngQ': Queue(),
            'jobMngQ': Queue(),
            'listenerQ': Queue(),
            'masterQ': Queue(),
            'cacheStoreQ': Queue(),
            'statusQ': Queue()
        }
        return q_pack

    def _del_process(self):
        try:
            # workerPool = self._sysContext['appProcInfo']['workerPool']
            # for appProId, appInfo in workerPool.items():
            #     self._logger.warn("Close Process: %s, PID: %d" %(appProId, appInfo['pid']))
            #     appInfo['process'].terminate()
            pass
        except KeyError as e:
            self._logger.warn('[Worker Pool] Shutdown')
        except KeyboardInterrupt as e:
            self._logger.warn('[Worker Pool] Shutdown')
        except Exception as e:
            self._logger.exception(e)
        finally:
            sys.exit(1)

    def _runProcessWatcher(self, qPack):
        system_q = qPack['systemQ']
        while True:
            try:
                message = system_q.get()
                self._logger.info(message)
                protocol = message.get('protocol')
            except KeyboardInterrupt as e:
                self._del_process()
                self._logger.warn("[Process Manager] Shutdown")
                break
            except Exception as e:
                self._del_process()
                break

    def doProcess(self):
        try:
            qPack = self._gen_queue_pack()
            launcher = ProcessLauncher(self._logger, self._sysContext)
            launcher.launch_process(qPack)
            self._runProcessWatcher(qPack)
        except KeyboardInterrupt as e:
            self._logger.warn("[Launcher] Shutdown")
        except Exception as e:
            self._logger.exception(e)
