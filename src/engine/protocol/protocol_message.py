#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.util_common import genJobId, gen_req_id

def genJobContext(jobOrder, appCode, isReturn, params={}, schedId=None):
    jobContext = {
        'jobId': genJobId(appCode),
        'appCode': appCode,
        'jobOrder': jobOrder,
        'schedId': schedId,
        'params': params,
        'isReturn': isReturn
    }
    return jobContext


def genServiceContext(jobOrder, appCode, jobType):
    jobContext = {
        'jobOrder': jobOrder,
        'appCode': appCode,
        'jobType': jobType,
    }
    return jobContext

# --------------------------------------------------------------------- #
# Realtime Job Protocol #
def genRealtimeJobOrder(jobReqType, jobContext):
    message = {
        'protocol': 'REQ_START_RT_JOB',
        'statCode': 300,
        'jobReqType': jobReqType,
        'jobContext': jobContext
    }
    return message

# --------------------------------------------------------------------- #
# Ondemand Job Protocol #
def genOndemandJobOrder(jobReqType, jobContext, returnPath, isReturn, requester='api'):
    message = {
        'protocol': 'REQ_ONDEMAND_JOB_ORDER',
        'statCode': 300,
        'jobReqType': jobReqType,
        'jobContext': jobContext,
        'returnPathList': [returnPath],
        'isReturn': isReturn,
        'requester': requester
    }
    return message

# --------------------------------------------------------------------- #
# Batch Job Protocol #
def genBatchJobOrder(jobReqType, jobContext, returnPath, isReturn, requester='api'):
    message = {
        'protocol': 'REQ_BATCH_JOB_ORDER',
        'statCode': 300,
        'jobReqType': jobReqType,
        'jobContext': jobContext,
        'returnPathList': [returnPath],
        'isReturn': isReturn,
        'requester': requester
    }
    return message

# --------------------------------------------------------------------- #
# Permanent Job Protocol #
def genPermanentJob(serviceContext):
    message = {
        'protocol': 'REQ_CREATE_PERMANENT_JOB',
        'statCode': 300,
        'serviceContext': serviceContext
    }
    return message

# --------------------------------------------------------------------- #
# Master Protocol #
def genDropWorker(serviceId):
    message = {
        'protocol': 'REQ_DROP_WORKER',
        'statCode': 300,
        'serviceId': serviceId
    }
    return message

def genDropDriver(serviceId):
    message = {
        'protocol': 'REQ_DROP_DRIVER',
        'statCode': 300,
        'serviceId': serviceId
    }
    return message

def genDropExecutor(executorId, serviceId=None):
    message = {
        'protocol': 'REQ_DROP_EXECUTOR',
        'statCode': 300,
        'serviceId': serviceId,
        'executorId':executorId
    }
    return message

# --------------------------------------------------------------------- #
# Driver Protocol #
def genDriverJobOrder(jobContext):
    message = {
        'protocol': 'REQ_RUN_JOB',
        'statCode': 300,
        'jobContext': jobContext
    }
    return message

def genAddTask(jobId, appCode, params):
    message = {
        'protocol': 'REQ_ADD_TASK',
        'statCode': 300,
        'jobId': jobId,
        'appCode': appCode,
        'params': params
    }
    return message

def genStopTask(jobId):
    message = {
        'protocol': 'REQ_STOP_TASK',
        'statCode': 300,
        'jobId': jobId
    }
    return message

def genStopJob(jobId, executorId):
    message = {
        'protocol': 'REQ_STOP_JOB',
        'statCode': 300,
        'jobId': jobId,
        'executorId': executorId
    }
    return message

def genTaskContext(appCode, jobId, taskId, params):
    message = {
        'appCode': appCode,
        'jobId': jobId,
        'taskId': taskId,
        'params': params
    }
    return message

def genRunTask():
    message = {
        'protcol': 'REQ_RUN_TASK',
        'statCode': 300
    }

def genRunExecutor(taskContext, serviceId=None, executorId=None):
    message = {
        'protocol': 'REQ_RUN_EXECUTOR',
        'statCode': 300,
        'taskContext': taskContext,
        'serviceId': serviceId,
        'executorId': executorId
    }
    return message

def genGetResult(appCode):
    message = {
        'protocol': 'REQ_TASK_RESULT',
        'statCode': 300,
        'appCode': appCode
    }
    return message

def genSendTaskResult(resultSet):
    message = {
        'result': resultSet
    }
    return message

def genDropService(serviceId):
    message = {
        'protocol': 'REQ_DROP_SERVICE',
        'statCode': 300,
        'serviceId': serviceId
    }
    return message

def genCompletedJob(jobId, result=None):
    message = {
        'protocol': 'RES_COMPLETED_JOB',
        'statCode': 300,
        'jobId': jobId,
        'result': result
    }
    return message

def genReturnJobResult(jobId, result):
    message = {
        'protocol': 'RES_JOB_RESULT',
        'statCode': 300,
        'jobId': jobId,
        'result': result
    }
    return message

def genReturnDriverJobResult(jobId, result):
    message = {
        'protocol': 'RES_DRIVER_JOB_RESULT',
        'statCode': 300,
        'jobId': jobId,
        'result': result
    }
    return message

def genReqDriverOrderService(jobContext, requester='app', returnPath=(), isReturn=True):
    if requester not in ['app', 'api', 'driver']:
        raise RuntimeError('Not allowed "requester" type, It will be "app" or "api"')
    if not returnPath:
        returnPath = {'spotType': requester, 'spotId': genReqId()}
    message = {
        'protocol': 'REQ_DRIVER_JOB',
        'statCode': 300,
        'jobContext': jobContext,
        'returnPathList': [returnPath],
        'isReturn': isReturn,
        'requester': requester
    }
    return message

def genReqOrderService(jobContext, requester='app', returnPath=(), isReturn=True):
    if requester not in ['app', 'api']:
        raise RuntimeError('Not allowed "requester" type, It will be "app" or "api"')
    if not returnPath:
        returnPath = {'spotType': requester, 'spotId': genReqId()}
    message = {
        'protocol': 'REQ_ORDER_SERVICE',
        'statCode': 300,
        'jobContext': jobContext,
        'returnPathList': [returnPath],
        'isReturn': isReturn,
        'requester': requester
    }
    return message

def genResOrderService(returnPathList, result):
    message = {
        'protocol': 'RES_JOB_RESULT',
        'statCode': 300,
        'returnPathList': returnPathList,
        'result': result
    }
    return message

def genAddWorker(serviceId, jobId, appCode):
    message = {
        'protocol': 'REQ_ADD_WORKER',
        'statCode': 300,
        'serviceId': serviceId,
        'jobId': jobId,
        'appCode': appCode
    }
    return message

def genExecutorPool(jobId, jobExecutorMeta):
    message = {
        'protocol': 'RES_ADD_WORKER',
        'statCode': 300,
        'jobId': jobId,
        'jobExecutorMeta': jobExecutorMeta
    }
    return message


# --------------------------------------------------------------------- #
# Worker #


# --------------------------------------------------------------------- #
# Executor #
def genResCompleteTask(appCode, jobId, taskId, result):
    message = {
        'protocol': 'REQ_COMPLETED_TASK',
        'statCode': 300,
        'appCode': appCode,
        'jobId': jobId,
        'taskId': taskId,
        'result': result
    }
    return message


# --------------------------------------------------------------------- #
# System Job Protocol #
def genReqJobInfo(listenerId, reqId, jobId=None):
    message = {
        'protocol': 'REQ_JOB_INFO',
        'statCode': 300,
        'reqId': reqId,
        'listenerId': listenerId,
        'jobId': jobId
    }
    return message

def genResJobInfo(listenerId, reqId, resultInfo={}):
    message = {
        'protocol': 'RES_JOB_INFO',
        'statCode': 300,
        'reqId': reqId,
        'listenerId': listenerId,
        'resultInfo': resultInfo
    }
    return message

def genShutdownThread():
    message = {
        'protocol': 'SYS_SHUTDOWN',
        'statCode': 100
    }
    return message


# --------------------------------------------------------------------- #
def genCachedReload(repoCode, filePath, statCode=300):
    message = {
        'protocol': 'CACHE_RELOAD',
        'statCode': statCode,
        'orderInfo': {
            'repoCode': repoCode,
            'filePath': filePath
        }
    }
    return message

def genTaskInitStatus(jobContext):
    message = {
        'protocol': 'SYS_INIT_JOB_ORDER',
        'statCode': 300,
        'jobContext': jobContext
    }
    return message

# --------------------------------------------------------------------- #
# Scheduler #

def genStartScheduler(jobReqType, jobContexts, period):
    message = {
        'protocol': 'START_BJO_SCHED',
        'statCode': 100,
        'reqjobReqTypeId': jobReqType,
        'jobContexts': jobContexts,
        'period': period
    }
    return message

def genResetScheduler(returnPath):
    message = {
        'protocol': 'RESET_JOB_SCHEDULER',
        'statCode': 100,
        'returnPathList': [returnPath]
    }
    return message

def genStopScheduler(jobReqType):
    message = {
        'protocol': 'STOP_JOB_SCHED',
        'statCode': 100,
        'jobReqType': jobReqType
    }
    return message

def genStopAllScheduler(jobReqType):
    message = {
        'protocol': 'STOP_ALL_JOB_SCHED',
        'statCode': 100
    }
    return message