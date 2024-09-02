from __future__ import annotations

import asyncio
import traceback

import nonebot

from ..core import app
from .qzone import api as qzone_api
from .render import apirender
from . import preproc


class SocialPlatformManager:
    
    ap: app.Application

    platform_api: qzone_api.QzoneAPI

    current_invalid_cookies: dict = None

    renderer: apirender.IdoknowAPIRender

    invalid_count: int = 0

    preprocessor: preproc.PostPreprocessor

    publishing_semaphore: asyncio.Semaphore = asyncio.Semaphore(1)
    """发布信号量，防止同时发布多个稿件"""

    def __init__(self, ap: app.Application):
        self.ap = ap
        self.platform_api = qzone_api.QzoneAPI(ap)
        self.renderer = apirender.IdoknowAPIRender(ap)
        self.preprocessor = preproc.PostPreprocessor(ap)
    
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
        if self.platform_api.cookies != self.current_invalid_cookies:

            if not await self.platform_api.token_valid():

                self.invalid_count += 1

                if self.invalid_count < 3:
                    nonebot.logger.info("QQ空间cookies已失效，但是未达到3次，不发送通知。")
                else:

                    nonebot.logger.info("QQ空间cookies已失效，发送通知。")

                    asyncio.create_task(self.ap.imbot.send_private_message(
                        self.ap.config.data['campux_qq_admin_uin'],
                        "QQ空间cookies已失效，请发送 #更新cookies 命令进行重新登录。"
                    ))

                    self.current_invalid_cookies = self.platform_api.cookies
            else:
                self.invalid_count = 0

    async def can_operate(self) -> bool:
        return await self.platform_api.token_valid()

    async def publish_post(self, post_id: int):
        # 强制延迟
        await asyncio.sleep(self.ap.config.data['campux_publish_post_time_delay'])

        max_retry = 3

        async with self.publishing_semaphore:
            for i in range(max_retry):
                try:
                    await self._publish_post(post_id)
                    asyncio.create_task(self.ap.imbot.send_group_message(
                        self.ap.config.data['campux_review_qq_group_id'],
                        f"已成功发表：#{post_id}"
                    ))
                    return
                except Exception as e:
                    nonebot.logger.error(f"发表稿件失败：{traceback.format_exc()}")

                    await self.ap.cpx_api.post_post_log(
                        post_id,
                        op=0,
                        old_stat="in_queue",
                        new_stat="in_queue",
                        comment=f"{self.ap.config.data['campux_qq_bot_uin']} 发表失败({i}): {str(e)}"
                    )

                    if i == max_retry - 1:
                        asyncio.create_task(self.ap.imbot.send_group_message(
                            self.ap.config.data['campux_review_qq_group_id'],
                            f"发表失败：#{post_id}\n{str(e)}"
                        ))
                    else:
                        await asyncio.sleep(5)

    async def _publish_post(self, post_id: int):

        post = await self.ap.cpx_api.get_post_info(post_id)

        post = await self.preprocessor.preprocess_post(post)

        images_to_post = []

        images_to_post.append(
            await self.renderer.render(post)
        )

        for image_key in post.images:
            image = await self.ap.cpx_api.download_image(image_key)
            images_to_post.append(image)

        tid = await self.platform_api.publish_emotion(
            post.extra_text,
            images_to_post
        )

        # 记录log
        await self.ap.cpx_api.post_post_log(
            post_id,
            op=0,
            old_stat="in_queue",
            new_stat="in_queue",
            comment=f"{self.ap.config.data['campux_qq_bot_uin']} 发表稿件"
        )

        # 提交post verbose
        await self.ap.cpx_api.submit_post_verbose(
            post_id,
            key=str(self.platform_api.get_account_id()),
            values={
                "tid": tid
            }
        )

        # 通知到hash 
        await self.ap.mq.mark_post_published(post_id)

