from __future__ import annotations

import asyncio
import threading
import os

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

    config: config_mgr.ConfigManager
    
    cpx_api: api.CampuxAPI

    mq: redis.RedisStreamMQ

    redis_name_proxy: redis.RedisNameProxy

    social: social_mgr.SocialPlatformManager

    imbot: imbot_mgr.IMBotManager

    bot_event_loop: asyncio.AbstractEventLoop = None

    async def run(self):

        def nonebot_thread():
            nonebot.run()

        threading.Thread(target=nonebot_thread).start()

def convert_env_var(
    env_var: str,
    value_type: type
) -> any:
    print(env_var)
    if value_type == int:
        return int(env_var)
    elif value_type == str:
        return str(env_var)
    elif value_type == bool:
        if env_var == 'true':
            env_var = 'True'
        elif env_var == 'false':
            env_var = 'False'
        return eval(env_var)
    elif value_type == list:
        return list(eval(env_var))
    elif value_type == dict:
        return dict(eval(env_var))

async def create_app() -> Application:

    # 元数据
    meta = await config_mgr.load_json_config(
        "data/metadata.json",
        template_name="templates/metadata.json"
    )

    await meta.load_config()
    await meta.dump_config()

    # 配置文件
    config = await config_mgr.load_json_config(
        "data/config.json",
        template_name="templates/config.json"
    )

    await config.load_config()

    # 读取环境变量进行替换, for config
    config_data = config.data.copy()

    # 读取环境变量进行替换, for config
    for key in config_data:
        env_value = os.environ.get(key)

        if env_value is None:
            env_value = os.environ.get(key.upper())

        if env_value is not None:
            config.data[key] = convert_env_var(env_value, value_type=type(config.data[key]))

    await config.dump_config()

    # 缓存管理器
    cache = cache_mgr.CacheManager()
    cache.load()

    ap = Application()
    ap.cache = cache
    ap.meta = meta
    ap.config = config

    cpx_api = api.CampuxAPI(ap=ap)
    ap.cpx_api = cpx_api

    import nonebot
    # 初始化 NoneBot
    nonebot.init(
        **config.data
    )

    # 注册适配器
    driver = nonebot.get_driver()
    driver.register_adapter(OnebotAdapter)

    # 在这里加载插件
    nonebot.load_plugin("campux.imbot.nbmod")  # 本地插件

    ap.bot_event_loop = asyncio.get_event_loop()

    ap.redis_name_proxy = redis.RedisNameProxy(ap)
    ap.mq = redis.RedisStreamMQ(ap)
    await ap.mq.initialize()
    ap.social = social_mgr.SocialPlatformManager(ap)
    await ap.social.initialize()
    ap.imbot = imbot_mgr.IMBotManager(ap)
    return ap
