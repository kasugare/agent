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

def getAccessPoolType(section='WORKFLOW', option='access_pool_type'):
    conf = getConfig()
    access_type = conf.get(section, option)
    return access_type

def getSecretKey(section='SECRETKEY', option='secret_key'):
    conf = getConfig()
    secret_key = conf.get(section, option)
    return secret_key

def getAiLandContext(section='AILAND'):
    conf = getConfig()
    host = conf.get(section, 'host')
    port = int(conf.get(section, 'port'))
    db = conf.get(section, 'db')
    user = conf.get(section, 'user')
    passwd = conf.get(section, 'passwd')
    dbContext = {
        'host': host,
        'port': port,
        'db': db,
        'user': user,
        'passwd': passwd
    }
    return dbContext

