#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

def getDownloadPath(section='ADAPTER'):
    conf = getConfig()
    downloadPath = conf.get(section, 'upload_dir_path')
    return downloadPath
