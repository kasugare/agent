#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser
import traceback
import sys
import os

CONF_FILENAME = "../conf/"
CONF_NAME = "system.conf"

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

def getHomeDir(section='HOME'):
    conf = getConfig()
    homeDir = conf.get(section, 'home_dir')
    return homeDir

def getLockDir(section='HOME'):
    conf = getConfig()
    homeDir = conf.get(section, 'lock_dir')
    return homeDir

def getRouteDir(section='HOME'):
    conf = getConfig()
    homeDir = conf.get(section, 'route_dir')
    return homeDir

def getRecipeDir(section='DAG'):
    conf = getConfig()
    homeDir = conf.get(section, 'dag_dir')
    return homeDir

def getRecipeFile(section='DAG'):
    conf = getConfig()
    fileName = conf.get(section, 'dag_file')
    return fileName
