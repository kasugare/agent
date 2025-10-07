#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.service.execute.workflow_executor import WorkflowExecutor
from api.workflow.protocol.protocol_message import WebSocketMessage
from uvicorn.protocols.utils import ClientDisconnected
from starlette.websockets import WebSocketDisconnect
from multiprocessing import Queue
import asyncio


class WebStreamHandler:
    def __init__(self, logger, ws_manager, datastore, metastore, taskstore):
        self._logger = logger
        self._stream_Q = Queue()
        self._job_Q = Queue()
        self._ws_manager = ws_manager
        self._datastore = datastore
        self._metastore = metastore
        self._taskstore = taskstore
        self._workflow_executor = WorkflowExecutor(logger, datastore, metastore, taskstore, self._job_Q)

    async def _run_workflow(self):
        context = {'query': '에이전트의 기본 구성 요소는?', 'request_id': '1234567890'}
        result = self._workflow_executor.run_workflow(context)
        return result

    async def run_stream(self, connection_id):
        try:
            while True:
                try:
                    client_message = await self._ws_manager.receive_message(connection_id)
                    self._logger.debug(client_message)
                    await self._ws_manager.send_message(connection_id, "test")
                    if client_message == 'call':
                        result = await self._run_workflow()
                        print(result)
                        await self._ws_manager.send_message(connection_id, result)


                except (WebSocketDisconnect, ClientDisconnected):
                    self._ws_manager.disconnect(connection_id)
                    break

                except Exception as e:
                    error_response = WebSocketMessage(type="error", payload={"message": e.__str__()}, request_id="")
                    self._ws_manager.send_message(connection_id, error_response)
                    break
        except RuntimeError as e:
            if str(e).startswith('Cannot call "receive" once a disconnect'):
                print("[INFO] Received after disconnect; ignoring")
            else:
                raise
        except Exception as e:
            self._logger.error(e)
