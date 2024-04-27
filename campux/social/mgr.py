from __future__ import annotations

import asyncio
import traceback

import nonebot

from ..core import app
from .qzone import api as qzone_api
from .render import apirender


class SocialPlatformManager:
    
    ap: app.Application

    platform_api: qzone_api.QzoneAPI

    current_invalid_cookies: dict = None

    renderer: apirender.IdoknowAPIRender

    def __init__(self, ap: app.Application):
        self.ap = ap
        self.platform_api = qzone_api.QzoneAPI(ap)
        self.renderer = apirender.IdoknowAPIRender(ap)
    
    async def initialize(self):
        async def schedule_loop():
            await asyncio.sleep(15)
            while True:
                asyncio.create_task(self.schedule_task())
                await asyncio.sleep(30)

        asyncio.create_task(schedule_loop())

    async def schedule_task(self):
        nonebot.logger.info("检查QQ空间cookies是否失效...")
        # 检查cookies是否失效
        if not await self.platform_api.token_valid() and self.platform_api.cookies != self.current_invalid_cookies:
            nonebot.logger.info("QQ空间cookies已失效，发送通知。")

            asyncio.create_task(self.ap.imbot.send_private_message(
                self.ap.config.campux_qq_admin_uin,
                "QQ空间cookies已失效，请发送 #更新cookies 命令进行重新登录。"
            ))

            self.current_invalid_cookies = self.platform_api.cookies

    async def can_operate(self) -> bool:
        return await self.platform_api.token_valid()

    async def publish_post(self, post_id: int):
        try:
            post = await self.ap.cpx_api.get_post_info(post_id)

            images_to_post = []

            images_to_post.append(
                await self.renderer.render(post)
            )

            for image_key in post.images:
                image = await self.ap.cpx_api.download_image(image_key)
                images_to_post.append(image)

            await self.platform_api.publish_emotion(
                f"#{post_id}",
                images_to_post
            )

            # 通知到群里
            asyncio.create_task(self.ap.imbot.send_group_message(
                self.ap.config.campux_review_qq_group_id,
                f"已成功发表：#{post.id}"
            ))
        except Exception as e:
            traceback.print_exc()
            asyncio.create_task(self.ap.imbot.send_group_message(
                self.ap.config.campux_review_qq_group_id,
                f"发表失败：#{post_id}\n{str(e)}"
            ))
