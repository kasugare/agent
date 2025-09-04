#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser
import traceback
import sys
import os

CONF_FILENAME = "../conf/"
CONF_NAME = "system.conf"

def get_config():
    src_path = os.path.dirname(CONF_FILENAME)
    ini_path = src_path + "/" + CONF_NAME

    if not os.path.exists(ini_path):
        print("# Cannot find system.conf in conf directory: %s" %src_path)
        sys.exit(1)

    conf = configparser.RawConfigParser()
    conf.read(ini_path)
    return conf

def get_oper_mode(section='OPERATION'):
    conf = get_config()
    operMode = conf.get(section, 'operation_mode')
    return operMode.upper()

def getHomeDir(section='HOME'):
    conf = get_config()
    homeDir = conf.get(section, 'home_dir')
    return homeDir

def getLockDir(section='HOME'):
    conf = get_config()
    homeDir = conf.get(section, 'lock_dir')
    return homeDir

def getRouteDir(section='HOME'):
    conf = get_config()
    homeDir = conf.get(section, 'route_dir')
    return homeDir

def getRecipeDir(section='DAG'):
    conf = get_config()
    homeDir = conf.get(section, 'dag_dir')
    return homeDir

def getRecipeFile(section='DAG'):
    conf = get_config()
    fileName = conf.get(section, 'dag_file')
    return fileName

def get_web_socket(section='WEB_SOCKET'):
    conf = get_config()
    hostIp = conf.get(section, 'host_ip')
    ports = [int(port) for port in conf.get(section, 'ports').split(',')]
    hostsInfo = [(hostIp, port) for port in ports]
    return hostsInfo

def get_net_buffSize(section='WEB_SOCKET'):
    conf = get_config()
    buffSize = int(conf.get(section, 'buffer_size'))
    return buffSize

def get_connection_pool(section='WEB_SOCKET'):
    conf = get_config()
    connPool = int(conf.get(section, 'connection_pool'))
    return connPool

def get_web_socket_infos(section = 'WEB_SOCKET'):
    hostsInfo = get_web_socket(section)
    buffSize = get_net_buffSize(section)
    connPool = get_connection_pool(section)
    netInfoList = []
    for hostInfo  in hostsInfo:
        netInfoList.append({
            'hostInfo': hostInfo,
            'buffSize': buffSize,
            'connPool': connPool
        })
    return netInfoList