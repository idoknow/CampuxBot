from __future__ import annotations

import asyncio

import nonebot

from ..core import app
from .qzone import api as qzone_api


class SocialPlatformManager:
    
    ap: app.Application

    platform_api: qzone_api.QzoneAPI

    current_invalid_cookies: dict = None

    def __init__(self, ap: app.Application):
        self.ap = ap
        self.platform_api = qzone_api.QzoneAPI(ap)
    
    async def initialize(self):
        async def schedule_loop():
            await asyncio.sleep(15)
            while True:
                asyncio.create_task(self.schedule_task())
                await asyncio.sleep(30)

        asyncio.create_task(schedule_loop())

    async def schedule_task(self):
        # 检查cookies是否失效
        if not await self.platform_api.token_valid() and self.platform_api.cookies != self.current_invalid_cookies:

            await self.ap.imbot.send_private_message(
                self.ap.config.campux_qq_admin_uin,
                "QQ空间cookies已失效，请发送 #更新cookies 命令进行重新登录。"
            )

            self.current_invalid_cookies = self.platform_api.cookies

    async def publish_post(self, post_id: int):
        pass
