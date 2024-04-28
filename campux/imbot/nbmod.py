import traceback

import nonebot
import nonebot.exception
from nonebot.rule import to_me
from nonebot.plugin import on_command, on_regex
from nonebot.adapters import Event
import nonebot.adapters.onebot.v11.message as message
import nonebot.adapters.onebot.v11.event as ob11_event
import asyncio

from ..api import api
from ..core import app


ap: app.Application = None

async def is_private(event: Event):
    return type(event) == ob11_event.PrivateMessageEvent

# ========= 私聊 =========
sign_up = on_command("注册账号", rule=to_me() & is_private, priority=10, block=True)
reset_password = on_command("重置密码", rule=to_me() & is_private, priority=10, block=True)

relogin_qzone = on_command("更新cookies", rule=to_me() & is_private, priority=10, block=True)

any_message = on_regex(r".*", rule=to_me() & is_private, priority=100, block=True)

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

# ========= 群聊 =========
async def is_group(event: Event):
    return type(event) == ob11_event.GroupMessageEvent

async def is_review_allow(event: Event):
    if type(event) == ob11_event.PrivateMessageEvent:
        return False
    return ap.config.campux_qq_group_review and int(event.group_id) == int(ap.config.campux_review_qq_group_id)

# #通过 [id]
approve_post = on_command("通过", rule=to_me() & is_group & is_review_allow, priority=10, block=True)

# #拒绝 <原因> [id]
reject_post = on_command("拒绝", rule=to_me() & is_group & is_review_allow, priority=10, block=True)

# 重发 <id>
resend_post = on_command("重发", rule=to_me() & is_group & is_review_allow, priority=10, block=True)

# 其他命令，发帮助信息
any_message_group = on_regex(r".*", rule=to_me() & is_group & is_review_allow, priority=100, block=True)


@approve_post.handle()
async def approve_post_func(event: Event):
    try:
        msg_text = event.get_message().extract_plain_text()
        
        params = msg_text.split(" ")[1:]

        if len(params) == 1:
            post_id = int(params[0])
            comment = ""

            post = await api.campux_api.get_post_info(post_id)

            if post is None:
                await approve_post.finish(f"稿件 #{post_id} 不存在")
            else:
                if post.status == "pending_approval":
                    await ap.cpx_api.review_post(post_id, "approve", comment)

                    # 打日志
                    await ap.cpx_api.post_post_log(
                        post_id,
                        int(event.get_user_id()),
                        "pending_approval",
                        "approved",
                        "群内审核通过"
                    )

                    await approve_post.finish(f"已通过 #{post_id}")
                else:
                    await approve_post.finish(f"稿件 #{post_id} 状态不是待审核")
        else:
            await approve_post.finish(ap.config.campux_review_help_message)
    except Exception as e:
        if isinstance(e, nonebot.exception.FinishedException):
            return
        traceback.print_exc()
        await approve_post.finish(str(e))

@reject_post.handle()
async def reject_post_func(event: Event):
    try:
        msg_text = event.get_message().extract_plain_text()
        
        params = msg_text.split(" ")[1:]

        if len(params) >= 2:
            post_id = int(params[-1])
            comment = " ".join(params[:-1])

            post = await api.campux_api.get_post_info(post_id)

            if post is None:
                await reject_post.finish(f"稿件 #{post_id} 不存在")
            else:
                if post.status == "pending_approval":
                    await ap.cpx_api.review_post(post_id, "reject", comment)

                    # 打日志
                    await ap.cpx_api.post_post_log(
                        post_id,
                        int(event.get_user_id()),
                        "pending_approval",
                        "rejected",
                        f"群内审核拒绝，原因：{comment}"
                    )

                    await reject_post.finish(f"已拒绝 #{post_id}")
                else:
                    await reject_post.finish(f"稿件 #{post_id} 状态不是待审核")
        else:
            await reject_post.finish(ap.config.campux_review_help_message)
    except Exception as e:
        if isinstance(e, nonebot.exception.FinishedException):
            return
        traceback.print_exc()
        await reject_post.finish(str(e))

@resend_post.handle()
async def resend_post_func(event: Event):
    try:
        msg_text = event.get_message().extract_plain_text()
        
        params = msg_text.split(" ")[1:]

        if len(params) == 1:
            post_id = int(params[0])

            post = await api.campux_api.get_post_info(post_id)

            if post is None:
                await resend_post.finish(f"稿件 #{post_id} 不存在")
            else:
                nonebot.logger.info(f"正在重发稿件 {post_id}")
                await ap.social.publish_post(post_id)
        else:
            await resend_post.finish(ap.config.campux_review_help_message)
    except Exception as e:
        if isinstance(e, nonebot.exception.FinishedException):
            return
        traceback.print_exc()
        await resend_post.finish(str(e))

@any_message_group.handle()
async def any_message_group_func(event: Event):
    await any_message_group.finish(ap.config.campux_review_help_message)
