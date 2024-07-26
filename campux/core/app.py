from __future__ import annotations

import asyncio
import threading

import requests
import nonebot, nonebot.config
from nonebot.adapters.onebot.v11 import Adapter as OnebotAdapter  # 避免重复命名

from ..api import api
from ..mq import redis
from ..social import mgr as social_mgr
from ..imbot import mgr as imbot_mgr
from ..common import cache as cache_mgr
from ..config import manager as config_mgr


class Application:

    cache: cache_mgr.CacheManager

    meta: config_mgr.ConfigManager
    
    @property
    def cpx_api(self) -> api.CampuxAPI:
        return api.campux_api

    @property
    def config(self) -> nonebot.config.Config:
        return nonebot.get_driver().config
    
    mq: redis.RedisStreamMQ

    social: social_mgr.SocialPlatformManager

    imbot: imbot_mgr.IMBotManager

    bot_event_loop: asyncio.AbstractEventLoop = None

    async def run(self):

        def nonebot_thread():
            nonebot.run()

        threading.Thread(target=nonebot_thread).start()

async def create_app() -> Application:

    # 注册适配器
    driver = nonebot.get_driver()
    driver.register_adapter(OnebotAdapter)

    # 在这里加载插件
    nonebot.load_plugin("campux.imbot.nbmod")  # 本地插件

    # 元数据
    meta = await config_mgr.load_json_config("data/metadata.json", template_data={
        "post_publish_text": "'#' + str(post_id)",
    })

    await meta.load_config()
    await meta.dump_config()

    # 缓存管理器
    cache = cache_mgr.CacheManager()
    cache.load()

    ap = Application()
    ap.cache = cache
    ap.meta = meta

    ap.bot_event_loop = asyncio.get_event_loop()

    ap.mq = redis.RedisStreamMQ(ap)
    await ap.mq.initialize()
    ap.social = social_mgr.SocialPlatformManager(ap)
    await ap.social.initialize()
    ap.imbot = imbot_mgr.IMBotManager(ap)
    return ap
