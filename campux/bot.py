import traceback

import nonebot
from nonebot.rule import to_me
from nonebot.plugin import on_command
from nonebot.adapters import Event

from . import api


sign_up = on_command("注册账号", rule=to_me(), priority=10, block=True)
reset_password = on_command("重置密码", rule=to_me(), priority=10, block=True)

@sign_up.handle()
async def sign_up_func(event: Event):
    
    # await sign_up.finish("注册成功~")
    try:
        pwd = await api.campux_api.sign_up(uin=int(event.get_user_id()))
        await sign_up.finish(f"注册成功，初始密码：\n{pwd}")
    except Exception as e:
        traceback.print_exc()
        await sign_up.finish(str(e))

@reset_password.handle()
async def reset_password_func():
    await reset_password.finish("重置密码成功~")
