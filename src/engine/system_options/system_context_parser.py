#!/usr/bin/env python
# -*- coding: utf-8 -*-

from optparse import OptionParser
from engine.system_options.context_validator import ContextValidator


class SystemContextParser:
    def __init__(self, logger):
        self._logger = logger
        self._options()

    def _options(self):
        usage = """usage: %prog [options] arg1,arg2 [options] arg3"""

        parser = OptionParser(usage=usage)
        parser.add_option("-v", "--version",
            action="store_true",
            dest="version",
            default=False,
            help="""show reovery system version""")

        parser.add_option("--OPER_MODE",
            action="store",
            type="string",
            dest="operMode",
            default="prod",
            help="""
            [use] --OPER_MODE=prod
            [options] dev, qa or prod
            [default]: %default"""
        )

        parser.add_option("--DEBUG",
            action="store_true",
            default=False,
            dest="debugMode",
            help="""use this option if it have been processed,
            it will operate in DEBUG mode.
            [use] --DEBUG
            [options] --DEBUG or None
            [default: %default"""
        )

        options, args = parser.parse_args()
        self._vaild_options(options, args)

    def _vaild_options(self, options, args):
        optVaildator = ContextValidator(self._logger, options, args)
        self._sysContext = optVaildator.check_options()

    def _get_system_context(self):
        self._showOptions()
        return self._sysContext

    def _showOptions(self):
        isDebugMode = self._sysContext['debugMode']
        self._logger.info("=" * 100)
        contextKeys = self._sysContext.keys()

        for contextKey in contextKeys:
            if contextKey == 'appMeta' or contextKey == 'repoMetaPool':
                self._logger.info('# %s:' %(contextKey.ljust(10)))
                contextMap = self._sysContext[contextKey]
                for metaKey in contextMap.keys():
                    self._logger.info('    -%s: %s' %(metaKey.ljust(10), str(contextMap[metaKey])))
            else:
                self._logger.info('    -%s: %s' %(contextKey.ljust(10), str(self._sysContext[contextKey])))

        self._logger.info("=" * 100)
