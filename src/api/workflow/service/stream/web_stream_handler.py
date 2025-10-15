#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.common.util_async_sync_bridge import AsyncSyncBridge
from api.workflow.service.execute.workflow_executor import WorkflowExecutor
from api.workflow.protocol.protocol_message import WebSocketMessage
from uvicorn.protocols.utils import ClientDisconnected
from starlette.websockets import WebSocketDisconnect
from multiprocessing import Queue
from threading import Thread
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
        self._workflow_executor = WorkflowExecutor(logger, datastore, metastore, taskstore, self._job_Q, self._stream_Q)

    def _run_workflow(self):
        context = {'query': '에이전트의 기본 구성 요소는?', 'request_id': '1234567890'}
        result = self._workflow_executor.run_workflow(context)
        return result

    def _run_send_status(self, connection_id, loop=None):
        while self._ws_manager:
            status_message = self._stream_Q.get()
            if isinstance(status_message, dict):
                AsyncSyncBridge.sync_to_async(self._ws_manager.send_message)(connection_id, status_message)
            else:
                break

    async def run_stream(self, connection_id):
        executor = Thread(target=self._run_send_status, args=(connection_id,), daemon=True)
        executor.start()

        try:
            while True:
                try:
                    client_message = await self._ws_manager.receive_message(connection_id)
                    await self._ws_manager.send_message(connection_id, f"run: {client_message}")
                    if client_message == 'call':
                        executor = Thread(target=self._run_workflow, args=(), daemon=True)
                        executor.start()
                        status_message = self._stream_Q.get()
                        await self._ws_manager.send_message(connection_id, status_message)
                except (WebSocketDisconnect, ClientDisconnected):
                    self._job_Q.put_nowait("SIGTERM")
                    self._ws_manager.disconnect(connection_id)
                    break
                except Exception as e:
                    self._job_Q.put_nowait("SIGTERM")
                    error_response = WebSocketMessage(type="error", payload={"message": e.__str__()}, request_id="")
                    self._ws_manager.send_message(connection_id, error_response)
                    break
        except RuntimeError as e:
            self._job_Q.put_nowait("SIGTERM")
            if str(e).startswith('Cannot call "receive" once a disconnect'):
                print("[INFO] Received after disconnect; ignoring")
            else:
                raise
        except Exception as e:
            self._job_Q.put_nowait("SIGTERM")
            self._logger.error(e)
