from __future__ import annotations
import asyncio
import time
import datetime
import traceback

from nonebot import logger
import redis.asyncio as redis

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

        streams_to_check = [
            self.ap.config.campux_redis_publish_post_stream,
            self.ap.config.campux_redis_new_post_stream
        ]

        for stream in streams_to_check:
            group_info = await self.redis_client.xinfo_groups(stream)

            group_names = [
                x['name'].decode('utf-8') for x in group_info
            ]

            if not self.ap.config.campux_redis_group_id in group_names:
                await self.redis_client.xgroup_create(
                    name=stream,
                    groupname=self.ap.config.campux_redis_group_id,
                    id='0',
                    mkstream=True
                )

        async def routine_loop():
            await asyncio.sleep(10)
            while True:
                await self.process_stream(self.ap.config.campux_redis_publish_post_stream, self.check_publish_post)
                await self.process_stream(self.ap.config.campux_redis_new_post_stream, self.check_new_post)
                await asyncio.sleep(10)

        asyncio.create_task(routine_loop())

    async def process_stream(self, stream: str, process_message_func: callable):
        try:
            logger.info(f"检查{stream}消息...")

            # 检查pending
            pending = await self.redis_client.xpending(
                stream,
                self.ap.config.campux_redis_group_id
            )

            if pending['pending'] > 0:

                logger.info(f"处理{stream}未确认的消息...")

                # 获取未确认的消息
                messages = await self.redis_client.xpending_range(
                    stream,
                    self.ap.config.campux_redis_group_id,
                    min='-',
                    max='+',
                    count=1
                )

                for message in messages:
                    message_id = message['message_id'].decode('utf-8')

                    # 获取消息
                    message = await self.redis_client.xrange(
                        stream,
                        min=message_id,
                        max=message_id
                    )

                    await process_message_func(message[0])

            else:
                streams = await self.redis_client.xreadgroup(
                    groupname=self.ap.config.campux_redis_group_id,
                    consumername=self.ap.config.campux_qq_bot_uin,
                    streams={stream: '>'},
                    count=1,
                    block=5000
                )

                # 检查是否有新的消息
                for stream in streams:
                    for message in stream[1]:
                        await process_message_func(message)
        except Exception as e:
            logger.error(f"处理{stream}消息时出现错误。")
            logger.error(e)
            traceback.print_exc()

    async def check_publish_post(self, message: tuple):
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

    async def check_new_post(self, message: tuple):
        logger.info("处理消息: {}".format(message))

        post_id = int(message[1][b'post_id'].decode('utf-8'))

        await self.ap.imbot.send_new_post_notify(post_id)

        await self.redis_client.xack(self.ap.config.campux_redis_new_post_stream, self.ap.config.campux_redis_group_id, message[0])
