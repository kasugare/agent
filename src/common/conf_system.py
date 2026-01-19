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

def getPromptRecipeFile(section='DAG'):
    conf = getConfig()
    fileName = conf.get(section, 'prompt_dag_file')
    return fileName

def getAccessPoolType(section='WORKFLOW', option='access_pool_type'):
    conf = getConfig()
    access_type = conf.get(section, option)
    return access_type

def isMetaAutoLoad(section='WORKFLOW', option='auto_load'):
    conf = getConfig()
    is_auto_load = conf.get(section, option)
    if is_auto_load.lower() == 'true':
        is_auto_load = True
    else:
        is_auto_load = False
    return is_auto_load

def numOfBackupMetas(section='WORKFLOW', option='num_of_backup_metas'):
    conf = getConfig()
    try:
        num_of_backup_metas = int(conf.get(section, option))
    except Exception as e:
        num_of_backup_metas = 20
    return num_of_backup_metas

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

def getWorkflowTimeoutConfig(section='WORKFLOW_TIMEOUT'):
    conf = getConfig()
    max_retries = int(conf.get(section, 'max_retries'))
    timeout = float(conf.get(section, 'timeout'))
    delay_time = float(conf.get(section, 'delay_time'))
    exponential_backoff = conf.get(section, 'exponential_backoff')
    if exponential_backoff.lower() == 'true':
        exponential_backoff = True
    else:
        exponential_backoff = False

    timeout_config = {
        'max_retries': max_retries,
        'timeout': timeout,
        'delay_time': delay_time,
        'exponential_backoff': exponential_backoff
    }
    return timeout_config