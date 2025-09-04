#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time


def convertStringToBool(strData):
    if strData.upper() == 'TRUE':
        strData = True
    elif strData.upper() == 'FALSE':
        strData = False
    return strData

def convertPeriodToSec():
    pass

def convertTimeToSec():
    pass

def convertStringToNone():
    pass

def genJobId(appCode):
    jobId = "%s:%X" % (appCode, int(time.time() * 1000))
    return jobId

def gen_req_id():
    reqId = "REQ:%X" % int(time.time() * 1000)
    return reqId

def genServiceId(appCode):
    serviceId = "%s:SEV:%X" % (appCode, int(time.time() * 1000))
    return serviceId

def genDriverId(appCode):
    driverId = "%s:DRV:%X" % (appCode, int(time.time() * 1000))
    return driverId

def genWorkerId(appCode, pIndex):
    workerId = "%s:WRK_%d:%X" % (appCode, pIndex, int(time.time() * 1000))
    return workerId

def genExecutorId(appCode, pIndex, tIndex):
    executorId = "%s:EXC_%d-%d:%X" % (appCode, pIndex, tIndex, int(time.time() * 1000))
    return executorId

def genTaskId(jobId):
    executorId = "%s:TSK:%X" % (jobId, int(time.time() * 1000))
    return executorId

def getQueryString(queryPath):
    return None