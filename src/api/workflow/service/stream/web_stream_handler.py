#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.common.util_async_sync_bridge import AsyncSyncBridge
from api.workflow.service.execute.workflow_executor import WorkflowExecutor
from api.workflow.error_pool.error import NotDefinedProtocolMessage
from api.workflow.error_pool.error import InvalidInputException
from api.workflow.error_pool.error import UnauthorizedKeyError
from api.workflow.error_pool.error import NotDefinedWorkflowMetaException
from api.workflow.protocol.protocol_parser import ProtocolParser
from api.workflow.protocol.protocol_message import SYS_AUTH_KEY_MSG, RES_AUTH_KEY
from api.workflow.protocol.protocol_message import SYS_WF_RESULT_MSG, RES_WF_RESULT
from api.workflow.protocol.protocol_message import SYS_NODE_STATUS, RES_NODES_STATUS
from api.workflow.protocol.protocol_message import RES_NOT_ALLOWED_MSG, RES_UNAUTHRIZED_MSG, RES_INVALID_PARAMS_MSG, RES_EMPTY_META_MSG
from uvicorn.protocols.utils import ClientDisconnected
from starlette.websockets import WebSocketDisconnect
from multiprocessing import Queue
from threading import Thread
import hashlib
import time


class WebStreamHandler:
    def __init__(self, logger, ws_manager, datastore, metastore, taskstore):
        self._logger = logger
        self._stream_Q = Queue()
        self._job_Q = Queue()
        self._ws_manager = ws_manager
        self._datastore = datastore
        self._metastore = metastore
        self._taskstore = taskstore

        self._protocol = ProtocolParser(logger)
        self._workflow_executor = WorkflowExecutor(logger, datastore, metastore, taskstore, self._job_Q, self._stream_Q)

        self._auth_key_pool = {}
        self._req_message_pool = {}

    def _run_send_status(self, connection_id):
        def get_seesion_in_message(request_id):
            req_message = self._req_message_pool.get(request_id)
            session_id = req_message['header']['session_id']
            req_time = req_message['header']['timestamp']['req_time']
            return session_id, req_time

        while self._ws_manager:
            try:
                send_message = self._stream_Q.get()
                send_message = self._protocol.message_to_dict(send_message)
                self._logger.debug(f"[S->S] {send_message}")
                protocol = self._protocol.parse_system_protocl(send_message)

                if protocol == 'RES_AUTH_KEY':
                    request_id, result = self._protocol.parse_system_result_set(send_message)
                    session_id, req_time = get_seesion_in_message(request_id)
                    send_protocol_message = RES_AUTH_KEY(request_id, session_id, req_time, result)
                    del self._req_message_pool[request_id]

                elif protocol == 'RES_CHAT_QUERY':
                    request_id, result = self._protocol.parse_system_result_set(send_message)
                    session_id, req_time = get_seesion_in_message(request_id)
                    send_protocol_message = RES_WF_RESULT(request_id, session_id, req_time, result)

                elif protocol == "RES_NODE_STATUS":
                    request_id, result = self._protocol.parse_system_result_set(send_message)
                    session_id, req_time = get_seesion_in_message(request_id)
                    send_protocol_message = RES_NODES_STATUS(request_id, session_id, req_time, result)

                elif protocol in ['RES_EMPTY_META', 'RES_INVALID_PARAMS']:
                    send_protocol_message = send_message

                elif protocol == "SIGTERM":
                    self._close()
                    break
                else:
                    self._logger.warn(f"Wrong protocol: {protocol}")
                    continue

                self._logger.debug(f"[S->C] {send_protocol_message}")
                AsyncSyncBridge.sync_to_async(self._ws_manager.send_message)(connection_id, send_protocol_message)
            except Exception as e:
                self._logger.error(e)


    def _vaild_auth(self, message, reg_auth_key):
        message_header = message.get('header')
        try:
            auth_key = message_header['auth_key']
        except KeyError as e:
            raise NotDefinedProtocolMessage

        if not auth_key:
            raise NotDefinedProtocolMessage

        if auth_key != reg_auth_key:
            raise UnauthorizedKeyError

    def _run_gen_auth_key(self, request_id, connection_id: str):
        hash_object = hashlib.sha256()
        hash_object.update(connection_id.encode('utf-8'))
        auth_key = hash_object.hexdigest()
        self._auth_key_pool[connection_id] = auth_key
        send_protocol_message = SYS_AUTH_KEY_MSG(request_id, auth_key)
        self._stream_Q.put_nowait(send_protocol_message)

    def _run_workflow(self, request_id, connection_id):
        try:
            order_sheet = self._req_message_pool.get(request_id)
            range_map = order_sheet['payload']['range']
            start_node = range_map.get('from_node')
            end_node = range_map.get('to_node')
            params_map = order_sheet['payload']['params']
            question = params_map.get('question')
            context = {'query': question, 'request_id': request_id}
            result = self._workflow_executor.run_workflow(context, start_node=start_node, end_node=end_node)
            send_protocol_message = SYS_WF_RESULT_MSG(request_id, result)
            self._stream_Q.put_nowait(send_protocol_message)

        except AttributeError:
            error_message = RES_INVALID_PARAMS_MSG("InvalidInputParametersException", "Invalid input params")
            self._logger.warn(error_message)
            self._stream_Q.put_nowait(error_message)
        except NotDefinedWorkflowMetaException as e:
            error_message = RES_EMPTY_META_MSG(e.error_code(), e.__str__())
            self._logger.warn(error_message)
            self._stream_Q.put_nowait(error_message)
        except InvalidInputException as e:
            error_message = RES_INVALID_PARAMS_MSG(e.error_code(), e.__str__())
            self._logger.warn(error_message)
            self._stream_Q.put_nowait(error_message)
        except KeyError as e:
            self._logger.error(e)
            self._logger.error(self._req_message_pool.get(request_id))
            raise NotDefinedProtocolMessage

    def _run_nodes_status(self, request_id):
        nodes_status_info = {}
        self._stream_Q.put_nowait(nodes_status_info)

    def _close(self, connection_id=None):
        try:
            if connection_id:
                self._auth_key_pool.pop(connection_id, None)
            self._job_Q.put_nowait("SIGTERM")
            self._stream_Q.put_nowait("SIGTERM")
        except Exception as e:
            pass

    async def run_stream(self, connection_id):
        executor = Thread(target=self._run_send_status, args=(connection_id,), daemon=True)
        executor.start()

        try:
            while True:
                try:
                    client_message = await self._ws_manager.receive_message(connection_id)
                    client_message = self._protocol.message_to_dict(client_message)
                    self._logger.debug(f"[C->S] {client_message}")

                    protocol, request_id = self._protocol.parse_client_protocol(client_message)
                    self._req_message_pool[request_id] = client_message

                    if protocol == 'REQ_AUTH_KEY':
                        executor = Thread(target=self._run_gen_auth_key, args=(request_id, connection_id), daemon=True)
                        executor.start()
                    elif protocol == 'REQ_CHAT_QUERY':
                        auth_key = self._auth_key_pool.get(connection_id)
                        self._vaild_auth(client_message, auth_key)
                        executor = Thread(target=self._run_workflow, args=(request_id, connection_id), daemon=True)
                        executor.start()
                    elif protocol == 'REQ_NODES_STATUS':
                        self._run_nodes_status(request_id)
                    else:
                        self._logger.warn(f"Not defined protocol: {protocol}")
                except NotDefinedWorkflowMetaException as e:
                    error_message = RES_EMPTY_META_MSG(e.error_code(), e.__str__())
                    self._logger.warn(error_message)
                    await self._ws_manager.send_message(connection_id, error_message)
                except InvalidInputException as e:
                    error_message = RES_INVALID_PARAMS_MSG(e.error_code(), e.__str__())
                    self._logger.warn(error_message)
                    await self._ws_manager.send_message(connection_id, error_message)
                except NotDefinedProtocolMessage as e:
                    error_message = RES_NOT_ALLOWED_MSG(e.error_code(), e.__str__())
                    self._logger.warn(error_message)
                    await self._ws_manager.send_message(connection_id, error_message)
                except UnauthorizedKeyError as e:
                    error_message = RES_UNAUTHRIZED_MSG(e.error_code(), e.__str__())
                    self._logger.warn(error_message)
                    await self._ws_manager.send_message(connection_id, error_message)
                except (WebSocketDisconnect, ClientDisconnected):
                    self._close()
                    self._ws_manager.disconnect(connection_id)
                    break
                except Exception as e:
                    error_message = RES_NOT_ALLOWED_MSG(e.__str__(), str(e))
                    self._logger.warn(error_message)
                    await self._ws_manager.send_message(connection_id, error_message)
                    self._close()
        except RuntimeError as e:
            if str(e).startswith('Cannot call "receive" once a disconnect'):
                self._logger.error("Received after disconnect; ignoring")
            else:
                raise
        except Exception as e:
            self._logger.error(e)
        finally:
            self._close()
