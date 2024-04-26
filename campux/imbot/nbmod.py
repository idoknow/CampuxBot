import traceback

import nonebot
import nonebot.exception
from nonebot.rule import to_me
from nonebot.plugin import on_command, on_regex
from nonebot.adapters import Event
import nonebot.adapters.onebot.v11.message as message
import asyncio

from ..api import api
from ..core import app


ap: app.Application = None

sign_up = on_command("注册账号", rule=to_me(), priority=10, block=True)
reset_password = on_command("重置密码", rule=to_me(), priority=10, block=True)

relogin_qzone = on_command("更新cookies", rule=to_me(), priority=10, block=True)

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

@relogin_qzone.handle()
async def relogin_qzone_func(event: Event):
    user_id = int(event.get_user_id())

    if user_id != ap.config.campux_qq_admin_uin:
        await relogin_qzone.finish("无权限")
        return

    async def qrcode_callback(content: bytes):
        asyncio.create_task(ap.imbot.send_private_message(
            ap.config.campux_qq_admin_uin,
            message=[
                message.MessageSegment.text("请使用QQ扫描以下二维码以登录QQ空间："),
                message.MessageSegment.image(content)
            ]
        ))

    try:
        await ap.social.platform_api.relogin(qrcode_callback)
    except Exception as e:
        if isinstance(e, nonebot.exception.FinishedException):
            return
        traceback.print_exc()
        await relogin_qzone.finish(str(e))

@any_message.handle()
async def any_message_func(event: Event):
    await any_message.finish(nonebot.get_driver().config.campux_help_message)
