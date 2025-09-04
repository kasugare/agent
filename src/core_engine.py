#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.util_logger import Logger
from engine.system_options.system_context_parser import SystemContextParser
from engine.process.process_manager import ProcessManager


class WorkflowCoreEngine:
    def __init__(self, logger = None):
        if logger is not None:
            self._logger = logger
        else:
            self._logger = Logger("CORE_ENGINE").getLogger()
        self._sysContext = SystemContextParser(self._logger)._get_system_context()

    def run(self):
        process_manager = ProcessManager(self._logger, self._sysContext)
        process_manager.doProcess()


if __name__ == '__main__':
    engine = WorkflowCoreEngine()
    engine.run()