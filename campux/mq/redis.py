from __future__ import annotations

import asyncio
import time

import redis.asyncio as redis
from nonebot import logger

from ..core import app


class RedisStreamMQ:

    ap: app.Application

    redis_client: redis.Redis

    relogin_notify_times: list[int] = []

    def __init__(self, ap: app.Application):
        self.ap = ap
        self.relogin_notify_times = []

    async def initialize(self):
        self.redis_client = redis.Redis(
            host=self.ap.config.campux_redis_host,
            port=self.ap.config.campux_redis_port,
            db=0,
            password=self.ap.config.campux_redis_password
        )

        # 创建xgroup
        # 检查是否存在同名group

        group_info = await self.redis_client.xinfo_groups(self.ap.config.campux_redis_publish_post_stream)

        group_names = [
            x['name'].decode('utf-8') for x in group_info
        ]

        if not self.ap.config.campux_redis_group_id in group_names:
            self.redis_client.xgroup_create(
                name=self.ap.config.campux_redis_publish_post_stream,
                groupname=self.ap.config.campux_redis_group_id,
                id='0',
                mkstream=True
            )

        async def routine_loop():
            await asyncio.sleep(10)
            while True:
                await self.check_publish_post()
                await asyncio.sleep(30)

        asyncio.create_task(routine_loop())

    async def check_publish_post(self):
        try:
            logger.info("检查稿件发送请求消息...")

            # 检查pending
            pending = await self.redis_client.xpending(
                self.ap.config.campux_redis_publish_post_stream,
                self.ap.config.campux_redis_group_id
            )

            if pending['pending'] > 0:

                logger.info("处理未确认的消息...")

                # 获取未确认的消息
                messages = await self.redis_client.xpending_range(
                    self.ap.config.campux_redis_publish_post_stream,
                    self.ap.config.campux_redis_group_id,
                    min='-',
                    max='+',
                    count=1
                )

                for message in messages:
                    message_id = message['message_id'].decode('utf-8')

                    # 获取消息
                    message = await self.redis_client.xrange(
                        self.ap.config.campux_redis_publish_post_stream,
                        min=message_id,
                        max=message_id
                    )

                    await self.process_message(message[0])

            else:
                streams = await self.redis_client.xreadgroup(
                    groupname=self.ap.config.campux_redis_group_id,
                    consumername=self.ap.config.campux_qq_bot_uin,
                    streams={self.ap.config.campux_redis_publish_post_stream: '>'},
                    count=1,
                    block=5000
                )

                # 检查是否有新的发布稿件请求
                for stream in streams:
                    for message in stream[1]:
                        await self.process_message(message)
        except Exception as e:
            logger.error("处理发布稿件请求时出现错误。")
            logger.error(e)

    async def process_message(self, message: tuple):
        
        logger.info("处理消息: {}".format(message))

        post_id = int(message[1][b'post_id'].decode('utf-8'))

        if await self.ap.social.can_operate():
            await self.ap.social.publish_post(post_id)
            # 确认消息
            await self.redis_client.xack(self.ap.config.campux_redis_publish_post_stream, self.ap.config.campux_redis_group_id, message[0])
        else:
            now = time.time()

            if len(self.relogin_notify_times) == 0 or now - self.relogin_notify_times[-1] > 120*60:
                self.relogin_notify_times.append(now)
                asyncio.create_task(self.ap.imbot.send_private_message(
                    self.ap.config.campux_qq_admin_uin,
                    "空间cookies失效，当前有稿件待发布，请尽快更新cookies。"
                ))

            logger.warning("social模块未准备好，无法发布稿件。")