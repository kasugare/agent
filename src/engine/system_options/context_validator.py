#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.conf_version import get_version_info
from common.conf_system import get_web_socket_infos, get_oper_mode
import sys

class ContextValidator:
    def __init__(self, logger, options, args):
        self._logger = logger
        self._version_info = get_version_info()
        self._sys_context = self._set_sys_context(options, args)

        if self._sys_context['debugMode']:
            self._logger.setLevel('DEBUG')
        else:
            self._logger.setLevel('INFO')

    def _set_sys_context(Self, option, args):
        sys_context = {}
        if option.version != None:
            sys_context['version'] = option.version
        if option.operMode != None:
            sys_context['operMode'] = option.operMode
        if option.debugMode != None:
            sys_context['debugMode'] = option.debugMode
        return sys_context

    def check_options(self):
        self._logger.debug("# check user options ...")
        sys_context = {}
        sys_context['version'] = self._check_version()
        sys_context['debugMode'] = self._check_log_mode()
        sys_context['operMode'] = self._check_operation_mode()
        sys_context['netInfos'] = get_web_socket_infos()
        return sys_context

    def _check_version(self):
        if self._sys_context.get('version'):
            if 'version' in self._version_info:
                print(" - version: %s" %(self._version_info['version']))
            if 'update_date' in self._version_info:
                print(" - update date: %s" %(self._version_info['update_date']))
            if 'describe' in self._version_info:
                print(" - describe: %s" %(self._version_info['describe']))
            sys.exit(1)
        return self._version_info

    def _check_operation_mode(self):
        operMode = self._sys_context.get('operMode')
        if not operMode or operMode.lower() == 'none':
            return get_oper_mode()
        elif operMode.upper() in ['DEV', 'QA', 'PROD']:
            return operMode
        else:
            self._logger.error('exit: _check_operation_mode, \nCheck your operational mode')
            sys.exit(1)

    def _check_log_mode(self):
        return self._sys_context.get('debugMode')