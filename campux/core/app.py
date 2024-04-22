from __future__ import annotations

from ..api import api
from ..mq import redis
from ..social import mgr as social_mgr
from ..imbot import mgr as imbot_mgr


class Application:
    
    @property
    def cpx_api(self) -> api.CampuxAPI:
        return api.campux_api
    
    mq: redis.RedisStreamMQ

    social: social_mgr.SocialPlatformManager

    imbot: imbot_mgr.IMBotManager


def create_app() -> Application:
    ap = Application()
    ap.mq = redis.RedisStreamMQ(ap)
    ap.social = social_mgr.SocialPlatformManager(ap)
    ap.imbot = imbot_mgr.IMBotManager(ap)
    return ap