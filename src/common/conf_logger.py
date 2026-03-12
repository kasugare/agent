#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser
import sys
import os

CONF_PATH = "../conf/"
CONF_FILENAME = "logger.conf"

LOGGER_INFO = ('log_name', 'log_level', 'log_format', 'log_dir', 'log_filename')
HANDLER_INFO = ('is_stream', 'is_file')
LOTATE_INFO = ('is_lotate', 'log_maxsize', 'backup_count')

DATA_TYPE_MAP = {
	'timezone': 'str',
	'log_name': 'str',
	'log_level': 'str',
	'log_format': 'str',
	'log_dir': 'str',
	'log_filename': 'str',
	'is_stream': 'bool',
	'is_file': 'bool',
	'is_pipe': 'bool',
	'is_lotate': 'bool',
	'log_maxsize': 'int',
	'backup_count': 'int',
	'topic': 'str',
	'kafka_bootstrap_servers': 'str'
}


def _getConfig():
	src_path = os.path.dirname(CONF_PATH)
	ini_path = src_path + "/" + CONF_FILENAME

	if not os.path.exists(ini_path):
		print("# Cannot find logger.conf in conf directory: %s" %src_path)
		sys.exit(1)

	conf = configparser.RawConfigParser()
	conf.read(ini_path)
	return conf

def _hasSections(sections):
	conf = _getConfig()
	has_section = True
	for section in sections:
		if not conf.has_section(section):
			has_section = False
			break
	return has_section

def _cvtFlag(value):
	if value.lower() == 'true':
		return True
	elif value.lower() == 'false':
		return False
	else:
		print("# Wrong logger values in logger.conf.")
		sys.exit(1)


def _checkInteger(value):
	try:
		return int(value)
	except Exception as e:
		print("# Wrong logger values in logger.conf.")
		sys.exit(1)


def _getLoggerConf(configList, elemnts = LOGGER_INFO, confName = 'SYSTEM'):
	conf = _getConfig()
	for elementName in elemnts:
		configList[elementName] = conf.get(confName, elementName)
	return configList


def _getCommonHandlerConf(configList, elements = HANDLER_INFO, confName = 'COMMON_HANDLER'):
	conf = _getConfig()
	for elementName in elements:
		elementValue = conf.get(confName, elementName)

		if elementName == 'is_stream':
			configList[elementName] = _cvtFlag(elementValue)
		elif elementName == 'is_file':
			configList[elementName] = _cvtFlag(elementValue)
		else:
			configList[elementName] = elementValue
	return configList

def _getCommonLotateConf(configList, elemnts = LOTATE_INFO, confName = 'COMMON_LOTATE'):
	conf = _getConfig()
	for elementName in elemnts:
		elementValue = conf.get(confName, elementName)
		if elementName == 'is_lotate':
			configList[elementName] = _cvtFlag(elementValue)
		elif elementName == 'log_maxsize':
			configList[elementName] = _checkInteger(elementValue)
		elif elementName == 'backup_count':
			configList[elementName] = _checkInteger(elementValue)
		else:
			configList[elementName] = elementValue
	return configList

def _dataTypeConverter(dataType, value):
	converters = {
		'int': int,
		'float': float,
		'str': str,
		'bool': lambda v: v.lower() == 'true' if isinstance(v, str) else bool(v),
		'list': lambda v: eval(v) if isinstance(v, str) else list(v),
		'dict': lambda v: eval(v) if isinstance(v, str) else dict(v),
	}
	try:
		return converters[dataType](value)
	except KeyError:
		raise ValueError(f"Unsupported dataType: {dataType}")
	except Exception as e:
		raise ValueError(f"Conversion failed: {e}")

def _getAllLogConf(loggerConfName):
	configList = {}
	conf = _getConfig()
	conf_items = conf.items(loggerConfName)
	for conf_item in conf_items:
		key = conf_item[0]
		value = conf_item[1]
		dataType = DATA_TYPE_MAP.get(key, 'str')
		configList[key] = _dataTypeConverter(dataType, value)

	if configList.get('kafka_bootstrap_servers'):
		str_servers = configList.get('kafka_bootstrap_servers')
		server_list = str_servers.split(',')
		configList['kafka_bootstrap_servers'] = server_list
	return configList

def getLoggerInfo(loggerConfName):
	configList = _getAllLogConf(loggerConfName)

	return configList