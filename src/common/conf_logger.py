#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.conf_system import getAppId
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
	'kafka_bootstrap_servers': 'str',
	'kafka_group_id': 'str'
}

ENV_CONF_MAP = {
	'timezone': 'TIMEZONE',
	'log_level': 'LOG_LEVEL',
	'log_dir': 'LOG_FILE_PATH',
	'log_filename': 'LOG_FILE_NAME',
	'log_maxsize': 'LOG_FILE_MAX_SIZE',
	'backup_count': 'LOG_FILE_BACKUP_COUNT',
	'kafka_bootstrap_servers': 'LOG_KAFKA_BOOTSTRAP_SERVERS',
	'kafka_group_id': 'KAFKA_GROUP_ID',
	'topic': 'KAFKA_TOPIC'
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

def _getLogHandler():
	log_handler_list = []
	try:
		log_handlers = os.environ.get('LOG_HANDLERS')
		if log_handlers:
			splited_log_handlers = log_handlers.replace(" ","").split(',')
			for handler_name in splited_log_handlers:
				if handler_name.lower() == 'console':
					log_handler_list.append('is_stream')
				elif handler_name.lower() == 'file_handler':
					log_handler_list.append('is_file')
				elif handler_name.lower() == 'kafka_handler':
					log_handler_list.append('is_pipe')
	except:
		pass
	return log_handler_list

def _activateLogHandler(config_info):
	env_log_handler = _getLogHandler()
	target_handlers = ['is_stream', 'is_file', 'is_pipe']
	if not env_log_handler:
		return config_info
	act_handler = list(set(target_handlers).intersection(set(env_log_handler)))
	for act_handler_type in act_handler:
		if config_info.get(act_handler_type):
			config_info[act_handler_type] = True

	deact_handler = list(set(target_handlers).difference(set(env_log_handler)))
	for deact_handler_type in deact_handler:
		if config_info.get(deact_handler_type):
			config_info[deact_handler_type] = False
	return config_info

def _getAllLogConf(section):
	config_info = {}
	conf = _getConfig()
	conf_options = conf.options(section)
	for option in conf_options:
		if option.lower() == 'topic':
			app_id = os.environ.get('APP_ID', getAppId())
			config_info['app_id'] = app_id
			group_id = os.environ.get('GROUP_ID', conf.get(section, 'kafka_group_id'))
			if app_id and group_id:
				value = f'log-{group_id}-{app_id}'
			else:
				value = conf.get(section, option)
		else:
			option_key = ENV_CONF_MAP.get(option, option)
			def_value = conf.get(section, option)
			value = os.environ.get(option_key, def_value)

		dataType = DATA_TYPE_MAP.get(option, 'str')
		config_info[option] = _dataTypeConverter(dataType, value)

	if config_info.get('kafka_bootstrap_servers'):
		str_servers = config_info.get('kafka_bootstrap_servers')
		server_list = str_servers.split(',')
		config_info['kafka_bootstrap_servers'] = server_list

	return config_info

def getLoggerInfo(loggerConfName):
	config_info = _getAllLogConf(loggerConfName)
	config_info = _activateLogHandler(config_info)
	return config_info