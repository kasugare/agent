#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser
import sys
import os

CONF_FILENAME = "../conf/"
CONF_NAME = "version"

def get_config():
    src_path = os.path.dirname(CONF_FILENAME)
    conf_path = src_path + "/" + CONF_NAME

    if not os.path.exists(conf_path):
        print("# Cannot find version in conf directory: %s" %src_path)
        sys.exit(1)

    conf = configparser.RawConfigParser()
    conf.read(conf_path)
    return conf

def get_version_info(section='VERSION'):
    conf = get_config()
    version = conf.get(section, 'version')
    update_date = conf.get(section, 'update_date')
    versionDes = conf.get(section, 'describe')
    versionInfo = {
        'version': version,
        'update_date': update_date,
        'versionDes': versionDes
    }
    return versionInfo
