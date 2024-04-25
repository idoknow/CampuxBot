from __future__ import annotations

import nonebot

from ..core import app


class IMBotManager:
    
    ap: app.Application

    def __init__(self, ap: app.Application):
        self.ap = ap

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
