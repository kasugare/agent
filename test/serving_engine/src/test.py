#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ailand.common.logger import Logger

class test:
    def __init__(self):
        self._logger = Logger().getLogger()

    def doProcess(self):
        self._logger.info("TEST")
        self._logger.debug("TEST")

if __name__ == "__main__":
    t = test()
    t.doProcess()