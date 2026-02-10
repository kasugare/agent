# -*- coding: utf-8 -*-
# !/usr/bin/env python
from fastapi import FastAPI

from api.launcher.router.api_launcher_router import ApiLauncher


class EventHandler:
    def __init__(self, app: FastAPI):
        self.api_service_launcher = ApiLauncher(app)

    async def load_init_service(self):
        await self.api_service_launcher.load_init_service()
