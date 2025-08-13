#!/usr/bin/env python
# -*- coding: utf-8 -*-

from rainbow_logging_handler import RainbowLoggingHandler
import traceback
import logging.handlers
import logging
import sys
import os

ESSENTIAL_KEY = ('log_name', 'log_level', 'log_format')
def cast_bool(string):
	if str(string).upper() == 'TRUE':
		return True
	else:
		return False

LOG_ENV_FORMAT = {
	"log_name": str,
	"log_level": str,
	"log_format": str,
	"log_dir": str,
	"log_filename": str,
	"is_stream": cast_bool,
	"is_file": cast_bool,
	"is_lotate": cast_bool,
	"interval": int,
	"log_maxsize": int,
	"backup_count": int
}


class Logger:
	_loggerPool = {}

	def __new__(cls, loggerName='default', logEnv=None):
		logger = cls._loggerPool.get(loggerName)
		if logger is None:
			instance = super().__new__(cls)
			logger = instance._setup(logEnv)
			cls._loggerPool[loggerName] = logger
		return logger

	def __init__(self, loggerName=None, config=None):
		pass

	def _checkVaildEnv(self, logEnv):
		if not isinstance(logEnv, dict):
			print('# Wrong log-config format. so change your log-conf to default-conf. Please check your format')
			logEnv = self._defaultSet()

		if set(logEnv.keys()).intersection(ESSENTIAL_KEY) is not ESSENTIAL_KEY:
			print('# Not included essential key. It changed your log-conf to default-conf. Please check your config option')
			logEnv = self._defaultSet()

		try:
			logEnv = {key: type(logEnv.get(key)) for key, type in LOG_ENV_FORMAT.items()}
		except Exception as e:
			print('# Wrong log config types. It changed your log-conf to default-conf. Please check your config type')
			logEnv = self._defaultSet()

		return logEnv

	def _setup(self, logEnv=None):
		def extractLogFileInfo(logEnv):
			isFile = bool(logEnv.get('is_file'))
			if isFile:
				logMeta = {
					'filePath': os.path.join(logEnv.get('log_dir'), logEnv.get('log_filename')),
					'isLotate': cast_bool(logEnv.get('is_lotate')),
					'logFormat': str(logEnv.get('log_format')),
					'interval': int(logEnv.get('interval')),
					'maxBytes': int(logEnv.get('log_maxsize')) | 104857600,
					'backupCount': int(logEnv.get('backup_count')) | 30
				}
			else:
				logMeta = {}
			return logMeta

		loggerInfo = self._checkVaildEnv(logEnv)

		try:
			loggerName = loggerInfo.get('log_name')
			loggerLevel = self._getLevel(loggerInfo['log_level'])
			logger = logging.getLogger(loggerName)
			logger.setLevel(loggerLevel)

			if cast_bool(loggerInfo.get('is_file')):
				logFileMeta = extractLogFileInfo(loggerInfo)
				handler = self._setFileLoggingHandler(**logFileMeta)
				logger.addHandler(handler)

			if cast_bool(loggerInfo.get('is_stream')):
				logFormat = loggerInfo.get('log_format')
				handler = self._setStreamLoggingHandler(logFormat)
				logger.addHandler(handler)
			self._logger = logger
		except Exception as e:
			traceback.print_exc(e)
		return logger

	def _defaultSet(self):
		logConfig = {
			"log_name": "system_log",
			"log_level": "debug",
			"log_format": "%(asctime)s [%(process)d] [%(levelname)-5s] %(module)s.%(funcName)s() L%(lineno)d:: %(message)s",
			"log_dir": "log/",
			"log_filename": "system.log",
			"is_stream": "true",
			"is_file": "false",
			"is_lotate": "true",
			"interval": 1,
			"log_maxsize": 10485760,
			"backup_count": 10
		}
		return logConfig

	def _getLevel(self, level = "INFO"):
		logLevel = None
		level = level.upper()
		if level == "DEBUG":
			logLevel = logging.DEBUG
		elif level == "ERROR":
			logLevel = logging.ERROR
		elif level == "FATAL":
			logLevel = logging.FATAL
		elif level == "CRITICAL":
			logLevel = logging.CRITICAL
		elif level in ["WARN", "WARNING"]:
			logLevel =  logging.WARN
		elif level == "NOTSET":
			logLevel = logging.NOTSET
		else:
			logLevel = logging.INFO
		return logLevel

	def _setFileLoggingHandler(self, filePath, logFormat, isLotate=True, interval=1, maxBytes=104857600, backupCount=30):
		def mkdir(filePath):
			dirPath = os.path.abspath(os.path.dirname(filePath))
			if not os.path.exists(dirPath):
				os.makedirs(dirPath)

		mkdir(filePath)
		if isLotate:
			handler = logging.handlers.TimedRotatingFileHandler(filename=filePath, when="midnight", interval=interval, backupCount=backupCount)
		else:
			handler = logging.FileHandler(filePath)
		formatter = logging.Formatter(logFormat)
		handler.setFormatter(formatter)
		return handler

	def _setStreamLoggingHandler(self, logFormat):
		formatter = logging.Formatter(logFormat)
		handler = RainbowLoggingHandler(
			sys.stderr,
			datefmt 			= '%Y-%m-%d %H:%M:%S'
		)
		handler.setFormatter(formatter)
		return handler

	def setLevel(self, level = "INFO"):
		loggerLevel = self._getLevel(level)
		self._logger.setLevel(loggerLevel)

	def set_level(self, level = "INFO"):
		loggerLevel = self._getLevel(level)
		self._logger.setLevel(loggerLevel)

	def getLogger(self):
		return self._logger

	def get_logger(self):
		return self._logger

	@classmethod
	def get_instance(cls):
		return cls()

# logger = Logger.get_instance().get_logger()