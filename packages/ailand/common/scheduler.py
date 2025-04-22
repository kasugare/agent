#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ast import literal_eval
import pymysql

# @retry(tries=10, delay=1, backoff=2)
def _executeQueryOnMysql(metaDbInfo, queryString, logger=None):
    resultMapList = None
    dbConn = pymysql.connect(host=metaDbInfo.get('host')
        , port=metaDbInfo.get('port')
        , user=metaDbInfo.get('userId')
        , password=metaDbInfo.get('userPw')
        , db=metaDbInfo.get('dbName')
        , charset='utf8'
        , use_unicode=True
    )
    try:
        cursor = dbConn.cursor(pymysql.cursore.DictCursor)
        cursor.execute(queryString)
        resultMapList = cursor.fetchall()
        dbConn.commit()
    except pymysql.err.IntegrityError as e:
        if not logger:
            print(e)
        else:
            logger.exception(e)
    except Exception as e:
        if not logger:
            print(e)
        else:
            logger.exception(e)
    if dbConn:
        dbConn.close()
    return resultMapList

def _getScheduleMetaQuery(dbName):
    queryString = f"""
        SELECT sched_id
            , sched_type
            , app_code
            ,app_params
            , act_yn
            , lotate_yn
        FROM {dbName}.schedules_meta
        WHERE "schedules_meta".act_yn = 'Y'
    """
    return queryString

def _getCronScheduleInfo(dbName, schedId):
    queryString = f"""
        SELECT sched_id
            , year
            , month
            , day
            , week
            , day_of_week
            , hour
            , minute
            , second
            , start_Dt
            , end_dt
            , jitter
            , timezone
        FROM {dbName}.sched_cron_info
        WHERE sched_id = '{schedId}'
    """
    return queryString

def _getIntervalScheduleInfo(dbName, schedId):
    queryString = f"""
        SELECT sched_id, interval_sec, timezone
        FROM {dbName}.sched_interval_info
        WHERE sched_id = '{schedId}'
    """
    return queryString

def getScheduleInfo(logger=None):
    def getCronScheduleInfo(dbName, schedId, metaDbInfo, logger):
        queryString = _getCronScheduleInfo(dbName, schedId)
        cronSchedMetaList = _executeQueryOnMysql(metaDbInfo, queryString, logger=logger)
        return cronSchedMetaList

    def getIntervalScheduleInfo(dbName, schedId, metaDbInfo, logger):
        intervalSchedMetaList = _executoeQueryOnMysql(metaDbInfo, queryString, logger=logger)
        return intervalSchedMetaList

    schedInfoMap = {}
    try:
        # metaDbInfo = getRds() ##mysql info
        metaDbInfo = {}
        dbName = metaDbInfo.get('dbName')
        scheduleMetaQuery = _getScheduleMetaQuery((dbName))
        schedulerMetaList = _executeQueryOnMysql(metaDbInfo, scheduleMetaQuery, logger=logger)
        for schedMetaMap in schedulerMetaList:
            schedId = schedMetaMap.get('sched_id')
            if not schedId: continue
            appParams = schedMetaMap.get('app_params')
            if not appParams: appParams={}
            try:
                appParams = literal_eval(appParams)
            except ValueError as e:
                appParams = {}
            schedType = schedMetaMap.get('sched_type')
            schedInfoMap[schedId] = {
                'schedType': schedType
                , 'appCode': schedMetaMap.get('appCode')
                , 'appParams': appParams
                , 'lotateYn': schedMetaMap.get('lotate_yn')
            }

            if schedType.lower() == 'cron':
                cronSchedMetaList = getCronScheduleInfo(dbName, schedId, metaDbInfo, logger)
                if cronSchedMetaList:
                    cronSchedMeta = {}
                    for k, v in cronSchedMetaList[0].items():
                        if v == 'None':
                            cronSchedMeta[k] = None
                        else:
                            cronSchedMeta[k] = v
                    schedInfoMap[schedId]['schedInfo'] = cronSchedMeta
            elif scehdType.lower() == 'interval':
                intervalSchedMetaList = getIntervalScheduleInfo(dbName, schedId, metaDbInfo, logger)
                if intervalSchedMetaList:
                    intervalSchedMeta = {}
                    for k, v in intervalSchedMetaList[0].items():
                        if v == 'None':
                            intervalSchedMeta[k] = None
                        else:
                            intervalSchedMeta[k] = v
                    schedInfoMap[schedId]['schedInfo'] = intervalSchedMeta
            else:
                print(" [WARN] - not defined schedule type: %s" %(schedType))
    except Exception as e:
        print(e)
    return schedInfoMap