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
    config = os.environ.get(f"{section.upper()}_{option.upper()}", str(conf.get(section, option)))
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

def getOperMode(section='OPERATION', option='operation_mode'):
    operMode = _get_config(section, option)
    return operMode.upper()

def getHomeDir(section='HOME', option='home_dir'):
    homeDir = _get_config(section, option)
    return homeDir

def getLockDir(section='HOME', option='lock_dir'):
    lockDir = _get_config(section, option)
    return lockDir

def isServiceMetaReload(section='LAUNCHER', option='reload'):
    is_reload = _get_config(section, option)
    if is_reload.lower() == 'true':
        is_reload = True
    else:
        is_reload = False
    return is_reload

def getRemoteConnInfo(section='REMOTEPOOL'):
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

def getSecretKey(section='SECRETKEY', option='secret_key'):
    secret_key = _get_config(section, option)
    return secret_key

def getServerInfo(section='SERVER'):
    server_info = {}
    server_info['bind'] = str(_get_config(section, option='bind'))
    server_info['workers'] = int(_get_config(section, option='workers'))
    server_info['worker_class'] = str(_get_config(section, option='worker_class'))
    server_info['timeout'] = int(_get_config(section, option='timeout'))
    server_info['keepalive'] = int(_get_config(section, option='keepalive'))
    server_info['worker_connections'] = int(_get_config(section, option='worker_connections'))
    server_info['max_requests'] = int(_get_config(section, option='max_requests'))
    server_info['max_requests_jitter'] = int(_get_config(section, option='max_requests_jitter'))
    return server_info

def getEngineUrl(section='ENGINE'):
    baseUrl = _get_config(section, option='base_url')
    return baseUrl
