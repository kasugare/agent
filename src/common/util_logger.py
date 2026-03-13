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


class TZFormatter(logging.Formatter):
	def __init__(self, *args, tz=None, **kwargs):
		super().__init__(*args, **kwargs)
		self._tz = tz

	def formatTime(self, record, datefmt=None):
		dt = datetime.fromtimestamp(record.created, tz=pytz.utc).astimezone(self._tz)
		return dt.strftime('%Y-%m-%d %H:%M:%S.') + f'{record.msecs:03.0f}'  # ← 밀리초 추가


class CustomedRainbowHandler(RainbowLoggingHandler):
	def __init__(self, *args, converter=None, tz=None, **kwargs):
		super().__init__(*args, **kwargs)
		self._converter = converter
		self._tz = tz  # ← tz 저장

	def colorize(self, record):
		color_fmt = self._colorize_fmt(self._fmt, record.levelno)
		formatter = TZFormatter(color_fmt, tz=self._tz)
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
				import socket
				app_id = loggerInfo.get('app_id', '')
				hostname = socket.gethostname()
				namespace = ""
				topic = loggerInfo.get('topic', 'log')
				bootstrap_servers = loggerInfo.get('kafka_bootstrap_servers', [])
				group_id = loggerInfo.get('kafka_group_id', 'log')
				handler = self._setKafkaLoggingHandler(app_id, hostname, namespace, topic, group_id, bootstrap_servers, formatter)
				logger.addHandler(handler)
			except:
				print("# kafka_libraries are not installed: $> pip install kafka")
				print(" - not used log pipline mode")
		return logger

	def _getFormmater(self, logFormat, tz_code):
		tz = pytz.timezone(tz_code)
		formatter = TZFormatter(logFormat, tz=tz)
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
		handler = CustomedRainbowHandler(
			sys.stderr,
			converter=formatter.converter,
			tz=formatter._tz,
			color_lineno=('blue', None, True),
			color_funcName=('blue', None, True),
			color_asctime=('white', None, True)
		)
		handler.setFormatter(formatter)
		return handler

	def _setKafkaLoggingHandler(self, app_id, hostname, namespace, topic, group_id, bootstrap_servers, formatter):
		from kafka import KafkaProducer
		handler = KafkaLoggingHandler(
			KafkaProducer,
			app_id=app_id,
			hostname=hostname,
			namespace=namespace,
			bootstrap_servers=bootstrap_servers,
			topic=topic,
			group_id=group_id,
			formatter=formatter
		)
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
	def __init__(self, KafkaProducer, app_id, hostname, bootstrap_servers, topic, group_id=None, formatter=None, namespace=""):
		super().__init__()
		self._app_id = app_id
		self._hostname = hostname
		self._namespace = namespace

		self._topic = topic
		self._bootstrap_servers = bootstrap_servers
		self._create_topic_if_not_exists(topic, bootstrap_servers)
		self._producer = KafkaProducer(
			bootstrap_servers=bootstrap_servers,
			value_serializer=lambda v: json.dumps(v).encode('utf-8'),
			client_id=group_id,
		)
		if formatter:
			self.setFormatter(formatter)

	def _create_topic_if_not_exists(self, topic, bootstrap_servers, num_partitions=1, replication_factor=1):
		try:
			from kafka import KafkaConsumer

			consumer = KafkaConsumer(
				bootstrap_servers=bootstrap_servers,
				request_timeout_ms=5000,
				connections_max_idle_ms=10000
			)
			existing_topics = consumer.topics()
			print(f"# existing_topics: {existing_topics}")

			if topic not in existing_topics:
				from kafka import KafkaProducer
				temp_producer = KafkaProducer(bootstrap_servers=bootstrap_servers)
				temp_producer.send(topic, b'init')
				temp_producer.flush()
				temp_producer.close()
				print(f"# Kafka topic created: {topic}")
			else:
				print(f"# Kafka topic already exists: {topic}")

			consumer.close()

		except Exception as e:
			print(f"# Failed to create kafka topic: {str(e)}")

	def emit(self, record):
		try:
			splited_recode = self.format(record).split(' ')
			datetime = f"{splited_recode[0]} {splited_recode[1]}"
			log_entry = {
				'service_id': self._app_id,
				'namespace': self._namespace,
				'pod_name': self._hostname,
				'timestamp': datetime,
				'log_level': record.levelname,
				'module': record.module,
				'funcName': record.funcName,
				'lineno': record.lineno,
				'message': self.format(record),
			}
			self._producer.send(self._topic, log_entry)
			self._producer.flush()
		except Exception:
			self.handleError(record)

	def close(self):
		self._producer.close()
		super().close()