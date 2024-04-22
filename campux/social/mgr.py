from __future__ import annotations

from ..core import app


class SocialPlatformManager:
    
    ap: app.Application

    def __init__(self, ap: app.Application):
        self.ap = ap

    async def publish_post(self, post_id: int):
        pass
