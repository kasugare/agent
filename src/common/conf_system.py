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

def _get_config(section, option):
    conf = getConfig()
    config = os.environ.get(f"{section}_{option.upper()}", str(conf.get(section, option)))
    return config

def getAppId(section="ENV"):
    conf = getConfig()
    app_id = os.environ.get('APP_ID', conf.get(section, 'app_id'))
    return app_id


def getRouteAutoReload(section='LAUNCHER', option='reload'):
    isReload = _get_config(section, option)
    return isReload

def getRouteAccessType(section='LAUNCHER', option='access_type'):
    accessType = _get_config(section, option)
    return accessType

def getRouteDirPath(section='LAUNCHER', option='route_dir'):
    routeDirPath = _get_config(section, option)
    return routeDirPath

def getRouteFileName(section="LAUNCHER", option='route_file'):
    metaFileName = _get_config(section, option)
    return metaFileName

def getLaucherApis(section="LAUNCHER", option='active_apis'):
    str_apis = _get_config(section, option)
    str_apis = str_apis.replace(" ", "")
    act_apis = str_apis.split(",")
    return act_apis


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

def getRemoteConnInfo(section='REMOTEPOOL'):
    conf = getConfig()
    host = os.environ.get(f'{section}_ip', conf.get(section, 'ip'))
    port = int(os.environ.get(f'{section}_port', conf.get(section, 'port')))
    passwd = os.environ.get(f'{section}_password', conf.get(section, 'password'))
    ttl = int(os.environ.get(f'{section}_ttl', conf.get(section, 'ttl')))
    redisInfo = {
        'host': host,
        'port': port,
        'passwd': passwd,
        'ttl': ttl
    }
    return redisInfo

def getSecretKey(section='SECRETKEY', option='secret_key'):
    conf = getConfig()
    secret_key = conf.get(section, option)
    return secret_key

def getAiLandContext(section='AILAND'):
    conf = getConfig()
    host = os.environ.get(f'{section}_host', conf.get(section, 'host'))
    port = int(os.environ.get(f'{section}_port', conf.get(section, 'port')))
    db = os.environ.get(f'{section}_db', conf.get(section, 'db'))
    user = os.environ.get(f'{section}_user', conf.get(section, 'user'))
    passwd = os.environ.get(f'{section}_passwd', conf.get(section, 'passwd'))
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

def getServerInfo(section='SERVER'):
    conf = getConfig()
    server_info = {}
    server_info['bind'] = str(conf.get(section, 'bind'))
    server_info['workers'] = int(conf.get(section, 'workers'))
    server_info['worker_class'] = str(conf.get(section, 'worker_class'))
    server_info['timeout'] = int(conf.get(section, 'timeout'))
    server_info['keepalive'] = int(conf.get(section, 'keepalive'))
    server_info['worker_connections'] = int(conf.get(section, 'worker_connections'))
    server_info['max_requests'] = int(conf.get(section, 'max_requests'))
    server_info['max_requests_jitter'] = int(conf.get(section, 'max_requests_jitter'))
    return server_info

def getEngineUrl(section='ENGINE'):
    conf = getConfig()
    baseUrl = os.environ.get("ENGINE_BASE_URL", str(conf.get(section, 'base_url')))
    return baseUrl
