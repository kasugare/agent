#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser
import sys
import os
import traceback

CONF_FILENAME = "../conf/"
CONF_NAME = "workflow.conf"


def getConfig():
    src_path = os.path.dirname(CONF_FILENAME)
    ini_path = src_path + "/" + CONF_NAME

    if not os.path.exists(ini_path):
        print("# Cannot find system.conf in conf directory: %s" %src_path)
        sys.exit(1)

    conf = configparser.RawConfigParser()
    conf.read(ini_path)
    return conf

def _get_config(section, option):
    conf = getConfig()
    config = os.environ.get(f"{section}_{option.upper()}", str(conf.get(section, option)))
    return config

def setConfig(conf):
    src_path = os.path.dirname(CONF_FILENAME)
    ini_path = os.path.join(src_path, CONF_NAME)
    try:
        with open(ini_path, 'w') as f:
            conf.write(f)
    except Exception as e:
        print(traceback.format_exc(e))

def getOperMode(section='WORKFLOW'):
    operMode = _get_config(section, option='mode')
    return operMode.upper()


def setWorkflowId(section='ACTIVE_WORKFLOW', opt_value=None):
    if opt_value:
        conf = getConfig()
        conf.set(section, option='workflow_id', value=opt_value)
        setConfig(conf)

def getWorkflowId(section='ACTIVE_WORKFLOW'):
    workflow_id = _get_config(section, option='workflow_id')
    return workflow_id


def getRecipeDir(section='RECIPE'):
    homeDir = _get_config(section, option='dir_path')
    return homeDir


def getRecipeFile(section='RECIPE'):
    fileName = _get_config(section, option='file_name')
    return fileName


def getPromptRecipeFile(section='DAG'):
    fileName = _get_config(section, option='prompt_dag_file')
    return fileName


def getAccessPoolType(section='WORKFLOW', option='access_pool_type'):
    conf = getConfig()
    access_type = _get_config(section, option=option)
    return access_type


def getMetaPoolType(section='STORE_POOL', option='meta_pool_type'):
    access_type = _get_config(section, option=option)
    return access_type

def getMetaPoolDB(section='STORE_POOL', option='remote_meta_db'):
    try:
        redis_db = int(_get_config(section, option=option))
    except:
        redis_db = 1
    return redis_db

def getDataIoPoolType(section='STORE_POOL', option='data_io_pool_type'):
    access_type = _get_config(section, option=option)
    return access_type

def getDataIoPoolDB(section='STORE_POOL', option='remote_data_io_db'):
    try:
        redis_db = int(_get_config(section, option=option))
    except:
        redis_db = 2
    return redis_db


def getTaskPoolType(section='STORE_POOL', option='task_pool_type'):
    access_type = _get_config(section, option=option)
    return access_type

def getTaskPoolDB(section='STORE_POOL', option='remote_task_db'):
    try:
        redis_db = int(_get_config(section, option=option))
    except:
        redis_db = 3
    return redis_db


def isMetaAutoLoad(section='WORKFLOW', option='auto_load'):
    is_auto_load = _get_config(section, option=option)
    if is_auto_load.lower() == 'true':
        is_auto_load = True
    else:
        is_auto_load = False
    return is_auto_load

def getWorkflowTimeoutConfig(section='WORKFLOW_TIMEOUT'):
    max_retries = int(_get_config(section, option='max_retries'))
    timeout = float(_get_config(section, option='timeout'))
    delay_time = float(_get_config(section, option='delay_time'))
    exponential_backoff = _get_config(section, option='exponential_backoff')
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

def isWorkflowMetaAutoLoad(section='WORKFLOW'):
    auto_load = _get_config(section, option='auto_load')
    if auto_load.lower() == 'true':
        auto_load = True
    else:
        auto_load = False
    return auto_load

def isWorkflowMetaReload(section='WORKFLOW'):
    isReload = _get_config(section, option='reload')
    if isReload.lower() == 'true':
        isReload = True
    else:
        isReload = False
    return isReload

def numOfBackupMetas(section='WORKFLOW', option='num_of_backup_metas'):
    try:
        num_of_backup_metas = int(_get_config(section, option=option))
    except Exception as e:
        num_of_backup_metas = 20
    return num_of_backup_metas


def getRemoteConnInfo(section='WORKFLOW_REMOTEPOOL'):
    host = _get_config(section, option='ip')
    port = _get_config(section, option='port')
    passwd = _get_config(section, option='password')
    ttl = _get_config(section, option='ttl')
    redisInfo = {
        'host': host,
        'port': int(port),
        'passwd': passwd,
        'ttl': int(ttl)
    }
    return redisInfo

