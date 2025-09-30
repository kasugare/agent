#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import json
import uuid
from api.workflow.service.meta.meta_load_service import MetaLoadService
from api.workflow.service.data.data_store_service import DataStoreService
from api.workflow.service.task.task_load_service import TaskLoadService
from api.workflow.service.execute.action_planner import ActionPlanningService
from api.workflow.service.execute.workflow_execution_orchestrator import WorkflowExecutionOrchestrator
from api.workflow.common.websocket.ws_protocol import ClientMessage, ServerMessage
from api.workflow.workflow_schema import WebSocketMessage
from api.workflow.common.websocket.ws_connection_manager import WSConnectionManager
from starlette.responses import HTMLResponse
from starlette.websockets import WebSocketDisconnect
from pydantic import ValidationError
from multiprocessing import Queue
from typing import Dict, Any
from abc import abstractmethod
from fastapi import APIRouter, WebSocket


class BaseRouter:
    def __init__(self, logger=None, tags=[]):
        self._logger = logger
        self.router = APIRouter(tags=tags)
        self.setup_routes()

    @abstractmethod
    def setup_routes(self):
        pass

    def get_router(self) -> APIRouter:
        return self.router


class WorkflowEngine(BaseRouter):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, logger, db_conn=None):
        super().__init__(logger, tags=['serving'])
        self._datastore = DataStoreService(logger)
        self._taskstore = TaskLoadService(logger, self._datastore)
        self._metastore = MetaLoadService(logger, self._datastore)
        self._act_planner = ActionPlanningService(logger, self._datastore, self._metastore, self._taskstore)
        self._ws_connection_manager = WSConnectionManager()
        self._job_Q = Queue()
        self._act_meta = {}

    def _clean_all(self):
        self._datastore.clear()

    def setup_routes(self):
        @self.router.post(path='/workflow/meta')
        async def create_workflow(workflow) -> None:
            wf_meta = json.loads(workflow)
            self._clean_all()
            self._metastore.change_wf_meta(wf_meta)

        @self.router.post(path='/workflow/clear')
        async def call_data_clear():
            self._logger.error("################################################################")
            self._logger.error("#                         < Clear All >                        #")
            self._logger.error("################################################################")
            self._clean_all()

        @self.router.post(path='/workflow/run')
        async def call_chained_model_service(request: Dict[str, Any]):
            start_node = request.get('from')
            if start_node:
                request.pop('from')
            end_node = request.get('to')
            if end_node:
                request.pop("to")
            if request and 'request_id' in list(request.keys()):
                request_id = request.pop('request_id')
            else:
                request_id = "AUTO_%X" %(int(time.time() * 10000))
            request['request_id'] = request_id

            act_meta_pack = self._act_planner.gen_action_meta_pack(start_node, end_node, request)
            self._act_meta = act_meta_pack
            if act_meta_pack.get('act_start_nodes'):
                workflow_engine = WorkflowExecutionOrchestrator(self._logger, self._datastore, act_meta_pack, self._job_Q)
                result = workflow_engine.run_workflow(request)
            else:
                self._logger.error(f"# Not generated task_map, check DAG meta")
                result = "# Not generated task_map, check DAG meta"
            return {"result": result}

        @self.router.get(path='/workflow/metapack')
        async def call_meta_pack():
            self._logger.error("################################################################")
            self._logger.error("#                         < Meta Pack >                        #")
            self._logger.error("################################################################")
            meta_pack = self._datastore.get_meta_pack_service()
            for k, v in meta_pack.items():
                self._logger.debug(f" - {k} : \t{v}")
            return meta_pack

        @self.router.get(path='/workflow/datapool')
        async def call_data_pool():
            self._logger.error("################################################################")
            self._logger.error("#                         < Data Pool >                        #")
            self._logger.error("################################################################")
            data_pool = self._datastore.get_service_data_pool_service()
            for k, v in data_pool.items():
                self._logger.debug(f" - {k} : \t{v}")
            return data_pool

        @self.router.get(path='/workflow/act_dag')
        async def call_active_dag():
            self._logger.error("################################################################")
            self._logger.error("#                        < Active DAG >                        #")
            self._logger.error("################################################################")
            for k, v in self._act_meta.items():
                self._logger.info(f" - {k}")
                if isinstance(v, dict):
                    for kk, vv in v.items():
                        self._logger.debug(f" \t- {kk}: {vv}")
                elif isinstance(v, list):
                    for l in v:
                        self._logger.debug(f" \t- {l}")
                else:
                    self._logger.debug(f" \t- {v}")
                self._logger.debug("*" * 200)

        @self.router.get(path='/workflow/tasks')
        async def call_task_pool():
            self._logger.error("################################################################")
            self._logger.error("#                       < Active Tasks >                       #")
            self._logger.error("################################################################")
            act_task_map = self._act_meta.get('act_task_map')
            if not act_task_map:
                return
            for task_id, task_obj in act_task_map.items():
                self._logger.info(f" - {task_id}")
                service_id = task_obj.get_service_id()
                state = task_obj.get_state()
                env = task_obj.get_env_params()
                params = task_obj.get_params()
                result = task_obj.get_result()
                error = task_obj.get_error()
                node_type = task_obj.get_node_type()
                self._logger.debug(f"\t- service_id: {service_id}")
                self._logger.debug(f"\t- state:      {state}")
                self._logger.debug(f"\t- env:        {env}")
                self._logger.debug(f"\t- params:     {params}")
                self._logger.debug(f"\t- result:     {result}")
                self._logger.debug(f"\t- Error:      {error}")
                self._logger.debug(f"\t- node_type:  {node_type}")
                task_obj._print_service_info()
                self._logger.debug("*" * 100)

        @self.router.get("/")
        async def get():
            return HTMLResponse(html)

        @self.router.websocket("/ws/{user_id}")
        async def websocket_endpoint(websocket: WebSocket, user_id: str):
            await self._ws_connection_manager.connect(websocket, user_id)
            try:
                await self._ws_connection_manager.broadcast("system", f"{user_id} joined the chat")
                while True:
                    client_message = await websocket.receive_text()
                    self._logger.debug(client_message)

                    client_message = WebSocketMessage.model_validate_json(client_message)
                    request_id = client_message.request_id

                    if client_message.type == "init":
                        service_result = ""
                        init_response = WebSocketMessage(type="init", payload={"status": service_result}, request_id=request_id)
                        await self._ws_connection_manager.send_to_user(user_id=user_id, response=init_response)
                    elif client_message.type == "chat":
                        service_result = ""
                        chat_response = WebSocketMessage(type="chat", payload={"response": service_result}, request_id=request_id)
                        await self._ws_connection_manager.send_to_user(user_id=user_id, response=chat_response)
                    else:
                        error_response = WebSocketMessage(type="error", payload={"message": "Invalid protocol type"})
                        await self._ws_connection_manager.send_to_user(user_id=user_id, response=error_response)

            except WebSocketDisconnect:
                self._ws_connection_manager.disconnect(user_id)
                await self._ws_connection_manager.broadcast("system", f"{user_id} disconnected")

        html = """
        <!DOCTYPE html>
        <html>
          <body>
            <h2>Chat Room</h2>
            <div id="chat" style="height:200px; overflow:auto; border:1px solid #ccc;"></div>
            <helloworld id="msgInput" placeholder="Type message..." autofocus />
            <button onclick="sendMsg()">Send</button>
        
            <script>
          const userId = prompt("Enter your user_id");
          const ws = new WebSocket("ws://" + location.host + "/ws/" + userId);
          const chatBox = document.getElementById("chat");
          const helloworld = document.getElementById("msgInput");
        
          ws.onmessage = (e) => {
            try {
              const msg = JSON.parse(e.data);
              const el = document.createElement("div");
              el.textContent = `[${msg.user}] ${msg.text}`; // 이름 + 메시지 출력
              chatBox.appendChild(el);
              chatBox.scrollTop = chatBox.scrollHeight;
            } catch {
              console.warn("invalid msg:", e.data);
            }
          };
        
          function sendMsg() {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(helloworld.value);
              helloworld.value = "";
            }
          }
        </script>
        
          </body>
        </html>
        """