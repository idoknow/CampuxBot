import traceback

import nonebot
import nonebot.exception
from nonebot.rule import to_me
from nonebot.plugin import on_command, on_regex
from nonebot.adapters import Event

from ..api import api


sign_up = on_command("注册账号", rule=to_me(), priority=10, block=True)
reset_password = on_command("重置密码", rule=to_me(), priority=10, block=True)

any_message = on_regex(r".*", rule=to_me(), priority=100, block=True)

@sign_up.handle()
async def sign_up_func(event: Event):

    try:
        pwd = await api.campux_api.sign_up(uin=int(event.get_user_id()))
        await sign_up.finish(f"注册成功，初始密码：\n{pwd}")
    except Exception as e:
        if isinstance(e, nonebot.exception.FinishedException):
            return
        traceback.print_exc()
        await sign_up.finish(str(e))

@reset_password.handle()
async def reset_password_func(event: Event):
    try:
        pwd = await api.campux_api.reset_password(uin=int(event.get_user_id()))
        await reset_password.finish(f"重置成功，新密码：\n{pwd}")
    except Exception as e:
        if isinstance(e, nonebot.exception.FinishedException):
            return
        traceback.print_exc()
        await reset_password.finish(str(e))

@any_message.handle()
async def any_message_func(event: Event):
    await any_message.finish(nonebot.get_driver().config.campux_help_message)
