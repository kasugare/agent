#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser
import sys
import os

CONF_FILENAME = "../conf/"
CONF_NAME = "serving.conf"

def getConfig():
    src_path = os.path.dirname(CONF_FILENAME)
    ini_path = src_path + "/" + CONF_NAME

    if not os.path.exists(ini_path):
        print("# Cannot find system.conf in conf directory: %s" %src_path)
        sys.exit(1)

    conf = configparser.RawConfigParser()
    conf.read(ini_path)
    return conf


def getOperMode(section='OPERATION'):
    conf = getConfig()
    operMode = conf.get(section, 'operation_mode')
    return operMode.upper()


def getWorkflowId(section='WORKFLOW'):
    conf = getConfig()
    workflow_id = conf.get(section, 'workflow_id')
    return workflow_id