from __future__ import annotations

import asyncio
import threading

import requests
import nonebot, nonebot.config
from nonebot.adapters.onebot.v11 import Adapter as OnebotAdapter  # 避免重复命名
from nonebot.adapters.onebot.v11 import message

from ..api import api
from ..mq import redis
from ..social import mgr as social_mgr
from ..imbot import mgr as imbot_mgr
from ..common import cache as cache_mgr
from ..experimental import agent


class Application:

    cache: cache_mgr.CacheManager
    
    @property
    def cpx_api(self) -> api.CampuxAPI:
        return api.campux_api

    @property
    def config(self) -> nonebot.config.Config:
        return nonebot.get_driver().config
    
    mq: redis.RedisStreamMQ

    social: social_mgr.SocialPlatformManager

    imbot: imbot_mgr.IMBotManager

    ag: agent.ReviewAgent

    async def run(self):

        def nonebot_thread():
            nonebot.run()

        threading.Thread(target=nonebot_thread).start()

        await asyncio.sleep(10)

        result = await self.ag.get_ai_review(
            await self.cpx_api.get_post_info(108)
        )

        print(result)

async def create_app() -> Application:

    # 注册适配器
    driver = nonebot.get_driver()
    driver.register_adapter(OnebotAdapter)

    # 在这里加载插件
    nonebot.load_plugin("campux.imbot.nbmod")  # 本地插件

    # 缓存管理器
    cache = cache_mgr.CacheManager()
    cache.load()

    ap = Application()
    ap.cache = cache

    ap.mq = redis.RedisStreamMQ(ap)
    await ap.mq.initialize()
    ap.social = social_mgr.SocialPlatformManager(ap)
    await ap.social.initialize()
    ap.imbot = imbot_mgr.IMBotManager(ap)

    if ap.config.enable_review_agent:
        ap.ag = agent.ReviewAgent(ap)

    return ap
