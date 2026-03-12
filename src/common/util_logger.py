#!/usr/bin/env python
# -*- coding: utf-8 -*-

from rainbow_logging_handler import RainbowLoggingHandler
from common.conf_logger import getLoggerInfo
from datetime import datetime
import logging.handlers
import logging
import json
import pytz
import sys
import os


def tz_converter(tz):
    def converter(*args):
        utc_dt = datetime.now(tz=pytz.utc)
        return utc_dt.astimezone(tz).timetuple()
    return converter


class KSTRainbowHandler(RainbowLoggingHandler):
	def __init__(self, *args, converter=None, **kwargs):
		super().__init__(*args, **kwargs)
		self._converter = converter  # ← converter 저장

	def colorize(self, record):
		color_fmt = self._colorize_fmt(self._fmt, record.levelno)
		formatter = logging.Formatter(color_fmt, datefmt='%Y-%m-%d %H:%M:%S')
		if self._converter:
			formatter.converter = self._converter  # ← 주입된 converter 사용
		self.colorize_traceback(formatter, record)
		output = formatter.format(record)
		record.ext_text = None
		return output

class Logger:
	_loggerPool = {}

	def __new__(cls, confName='LOGGER', logEnv=None):
		logger = cls._loggerPool.get(confName)
		if logger is None:
			instance = super().__new__(cls)
			loggerInfo = getLoggerInfo(confName)
			logger = instance._setup(loggerInfo)
			cls._loggerPool[confName] = logger
		return logger

	def __init__(self, confName='LOGGER'):
		loggerInfo = getLoggerInfo(confName)
		self._logger = self._setup(loggerInfo)

	def _setup(self, loggerInfo):
		def_log_format = '%(asctime)s [%(process)d] [%(levelname)-5s] %(module)s.%(funcName)s() L%(lineno)d:: %(message)s'
		tz_code = loggerInfo.get('timezone', 'Asia/Seoul')
		loggerName = loggerInfo.get('log_name', 'system')
		logLevel = self._getLevel(loggerInfo.get('log_level', 'debug'))
		logFormat = loggerInfo.get('log_format', def_log_format)

		logger = logging.getLogger(loggerName)
		logger.setLevel(logLevel)
		formatter = self._getFormmater(logFormat, tz_code)

		isFile = loggerInfo.get('is_file', False)
		isStream = loggerInfo.get('is_stream', True)
		isPipe = loggerInfo.get('is_pipe', False)

		if isFile:
			try:
				dirPath = loggerInfo.get('log_dir', "/tmp/logs")
				if not os.path.exists(os.path.abspath(dirPath)):
					os.makedirs(dirPath)

				fileName = loggerInfo.get('log_filename', "system_logs")
				maxBytes = loggerInfo.get('log_maxsize', 10485760)
				backupCnt = loggerInfo.get('backup_count', 10)
				isLotate = loggerInfo.get('is_lotate', False)
				handler = self._setFileLoggingHandler(dirPath, fileName, formatter, isLotate, maxBytes, backupCnt)
				logger.addHandler(handler)
			except:
				print("# Unable to create log directory. Please check the permissions.")

		if isStream:
			handler = self._setStreamLoggingHandler(formatter)
			logger.addHandler(handler)

		if isPipe:
			try:
				topic = loggerInfo.get('topic', 'log')
				bootstrap_servers = loggerInfo.get('kafka_bootstrap_servers', [])
				handler = self._setKafkaLoggingHandler(topic, bootstrap_servers, formatter)
				logger.addHandler(handler)
			except:
				print("# kafka_libraries are not installed: $> pip install kafka")
				print(" - not used log pipline mode")
		return logger

	def _setKafkaLoggingHandler(self, topic, bootstrap_servers, formatter):
		from kafka import KafkaProducer
		handler = KafkaLoggingHandler(
			KafkaProducer,
			bootstrap_servers=bootstrap_servers,
			topic=topic,
			formatter=formatter
		)
		return handler

	def _getFormmater(self, logFormat, tz_code):
		formatter = logging.Formatter(logFormat)
		tz = pytz.timezone(tz_code)
		formatter.converter = tz_converter(tz)
		return formatter

	def _getLevel(self, level = "INFO"):
		level = level.upper()
		if level == "DEBUG":
			return logging.DEBUG
		elif level == "ERROR":
			return logging.ERROR
		elif level == "FATAL":
			return logging.FATAL
		elif level == "CRITICAL":
			return logging.CRITICAL
		elif level in ["WARN", "WARNING"]:
			return logging.WARN
		elif level == "NOTSET":
			return logging.NOTSET
		else:
			return logging.INFO

	def _setFileLoggingHandler(self, dirPath, fileName, formatter, isLotate=True, maxBytes=104857600, backupCnt=10):
		filePath = '%s/%s' %(dirPath, fileName)

		if isLotate:
			handler = logging.handlers.RotatingFileHandler(filePath, maxBytes=maxBytes, backupCount=backupCnt)
		else:
			handler = logging.FileHandler(filePath)
		handler.setFormatter(formatter)
		return handler

	def _setStreamLoggingHandler(self, formatter):
		handler = KSTRainbowHandler(
			sys.stderr,
			converter = formatter.converter,
			# datefmt 				= '%Y-%m-%d %H:%M:%S',
			# color_name				= ('white'	, None, True),
			# color_levelno			= ('white'	, None, False),
			# color_levelname			= ('white'	, None, True),
			# color_pathname			= ('blue'	, None, True),
			# color_filename			= ('blue'	, None, True),
			# color_module			= ('blue'	, None, True),
			color_lineno			= ('blue'	, None, True),
			color_funcName			= ('blue'	, None, True),
			# color_created			= ('white'	, None, False),
			color_asctime			= ('white'	, None, True),
			# color_msecs				= ('white'	, None, False),
			# color_relativeCreated	= ('white'	, None, False),
			# color_thread			= ('white'	, None, False),
			# color_threadName		= ('white'	, None, False),
			# color_process			= ('black'	, None, True),
			# color_message_debug		= ('cyan'	, None , False),
			# color_message_info		= ('white'	, None , False),
			# color_message_warning	= ('yellow'	, None , True),
			# color_message_error		= ('red'	, None , True),
			# color_message_critical	= ('white'	, 'red', True)
		)
		handler.setFormatter(formatter)
		return handler

	def setLevel(self, level:str = "INFO"):
		loggerLevel = self._getLevel(level)
		self._logger.setLevel(loggerLevel)

	def getLogger(self):
		return self._logger

	def set_level(self, level:str ="INFO"):
		self.setLevel(level)

	def get_logger(self):
		return self._logger

	#USE: logger = Logger.get_instance().get_logger()
	@classmethod
	def get_instance(cls):
		return cls()

class KafkaLoggingHandler(logging.Handler):
    def __init__(self, KafkaProducer, bootstrap_servers, topic, formatter=None):
        super().__init__()
        self._topic = topic
        self._producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        if formatter:
            self.setFormatter(formatter)

    def emit(self, record):
        try:
            log_entry = {
                'timestamp': self.format(record).split(' ')[0],  # asctime
                'level'    : record.levelname,
                'module'   : record.module,
                'funcName' : record.funcName,
                'lineno'   : record.lineno,
                'message'  : record.getMessage(),
            }
            self._producer.send(self._topic, log_entry)
            self._producer.flush()
        except Exception:
            self.handleError(record)

    def close(self):
        self._producer.close()
        super().close()