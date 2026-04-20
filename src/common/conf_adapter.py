#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.conf_system import getEngineUrl
import configparser
import sys
import os


CONF_FILENAME = "../conf/"
CONF_NAME = "adapter.conf"

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

def getDownloadPath(section='ADAPTER'):
    downloadPath = _get_config(section, option='upload_dir_path')
    return downloadPath

def getRemoteEngineUrl(section='REMOTE_ENGINE'):
    base_url = None
    try:
        base_url = _get_config(section, option='base_url')
    except Exception as e:
        pass
    finally:
        if not base_url:
            base_url = getEngineUrl()
    return base_url
