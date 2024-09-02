from __future__ import annotations

import asyncio
import datetime
import base64

import aiohttp
import nonebot
from nonebot import logger
import nonebot.adapters.onebot.v11.message as message

from ..core import app


class IMBotManager:
    
    ap: app.Application

    def __init__(self, ap: app.Application):
        self.ap = ap

    def image_to_base64(self, image: bytes) -> str:
        pic_base64 = base64.b64encode(image)

        return str(pic_base64)[2:-1]

    async def send_private_message(
        self,
        user_id: int,
        message
    ):
        bot = nonebot.get_bot()

        await bot.send_private_msg(
            user_id=user_id,
            message=message
        )

    async def send_group_message(
        self,
        group_id: int,
        message
    ):
        bot = nonebot.get_bot()

        await bot.send_group_msg(
            group_id=group_id,
            message=message
        )

    async def send_new_post_notify(
        self,
        post_id: int
    ):
        post = await self.ap.cpx_api.get_post_info(post_id)

        logger.info(f"新稿件：{post}")

        if self.ap.config.data['campux_qq_group_review']:

            # 获取所有图片
            images = [
                await self.ap.cpx_api.download_image(image_key)
                for image_key in post.images
            ]

            time_str = datetime.datetime.fromtimestamp(
                post.time_stamp).strftime("%Y-%m-%d %H:%M:%S")

            msg = [
                message.MessageSegment.text(f"新稿件: \n\n{post.text}\n\nID: #{post.id}\n用户: {'匿名( '+str(post.uin)+' )' if post.anon else post.uin}\n时间: {time_str}\n图片: {len(post.images)}张"),
            ]

            for image in images:
                msg.append(
                    message.MessageSegment.image(image)
                )
            
            asyncio.create_task(self.ap.imbot.send_group_message(
                self.ap.config.data['campux_review_qq_group_id'],
                msg
            ))

    async def send_post_cancel_notify(
        self,
        post_id: int
    ):
        logger.info(f"稿件已取消：{post_id}")

        if self.ap.config.data['campux_qq_group_review']:

            msg = [
                message.MessageSegment.text(f"稿件已取消: #{post_id}"),
            ]
            
            asyncio.create_task(self.ap.imbot.send_group_message(
                self.ap.config.data['campux_review_qq_group_id'],
                msg
            ))