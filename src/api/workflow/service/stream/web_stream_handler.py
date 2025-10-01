#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.protocol.protocol_message import WebSocketMessage
from uvicorn.protocols.utils import ClientDisconnected
from starlette.websockets import WebSocketDisconnect
import asyncio


class WebStreamHandler:
    def __init__(self, logger, ws_manager, datastore):
        self._logger = logger
        self._ws_manager = ws_manager

    def _execute_async(self, async_task):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(async_task)
            return result
        except Exception as e:
            self._logger.error(e)
        finally:
            loop.close()

    def run_stream(self, connection_id):
        try:
            while True:
                try:
                    client_message = self._execute_async(self._ws_manager.receive_text())
                    self._logger.debug(client_message)

                    client_message = WebSocketMessage.model_validate_json(client_message)
                    request_id = client_message.request_id
                    query = client_message.payload.query

                    if client_message.type == "init":
                        service_result = ""
                        init_response = WebSocketMessage(type="init", payload={"status": service_result},
                                                         request_id=request_id)
                        self._execute_async(self._ws_manager.send_text(init_response.model_dump_json()))
                    elif client_message.type == "chat":
                        print("request_id: ", request_id)
                        print("query: ", query)
                        # await call_chained_model_service({"request_id":request_id, "query": query})
                        # await asyncio.create_task(forward_queue_to_client(websocket, engine))
                    else:
                        error_response = WebSocketMessage(type="error",
                                                          payload={"message": "Invalid protocol type"})
                        self._execute_async(self._ws_manager.send_text(error_response.model_dump_json()))

                except (WebSocketDisconnect, ClientDisconnected):
                    self._ws_manager.disconnect(connection_id)
                    break

                except Exception as e:
                    error_response = WebSocketMessage(type="error", payload={"message": e.__str__()}, request_id="")
                    self._execute_async(self._ws_manager.send_text(error_response.model_dump_json()))
                    pass

        except RuntimeError as e:
            if str(e).startswith('Cannot call "receive" once a disconnect'):
                print("[INFO] Received after disconnect; ignoring")
            else:
                raise