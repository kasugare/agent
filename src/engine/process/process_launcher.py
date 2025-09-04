#!/usr/bin/env python
# -*- coding: utf-8 -*-

from engine.listener.api_listener_launcher import StasisApiListenerManager
import time
import sys


class ProcessLauncher:
    def __init__(self, logger, sysContext):
        self._logger = logger
        self._sysContext = sysContext
        self._listeners = []

    def _launch_listener(self, q_pack):
        self._logger.info("Start Listener")
        StasisApiListenerManager(self._logger, self._sysContext, q_pack).doLauncher()
        time.sleep(0.05)

    def launch_process(self, q_pack):
        try:
            self._launch_listener(q_pack)
        except KeyboardInterrupt as e:
            sys.exit(1)
        except Exception as e:
            self._logger.exception(e)
            sys.exit(1)
        return q_pack
