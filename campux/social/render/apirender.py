from __future__ import annotations

import datetime

import aiohttp

from ...core import app
from ...common import entity


jinja_template = """<!DOCTYPE html>
<html>

<head>
    <style>
        #nickname {
            font-weight: bold;
            font-size: 4.5rem;
            line-height: 1.2;
            margin-bottom: 0;
        }

        #words {
            font-family: Microsoft Yahei;
            font-size: 3.3rem;
            display: block;
            width: 65rem;
            margin-top: 4rem;
            word-spacing: 0.3rem;
            letter-spacing: 0.3rem;
            white-space: pre-wrap;
            overflow-wrap: break-word;
            word-wrap: break-word;
        }

        img {
            width: 18%;
            height: 18%;
            border-radius: 50%;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
        }

        #footer {
            display: flex;
            justify-content: space-between;
            width: 100%;
            padding: 0px 2rem;
            font-size: 2.2rem;
            margin: 1rem;
            color: #666
        }

        #bg-fixed-br {
            position: fixed;
            top: -120px;
            right: -170px;
            width: 500px;
            height: 500px;
            opacity: 0.25;
        }
    </style>
    <meta name="viewport" content="width=device-width,initial-scale=1.0">
</head>

<body style="margin: 0">
    <div id="title-bar" style="background-color: #1E88E5; height: 5%; width: calc(100% + 50px); padding: 16px; border-radius: 0 0 8px 8px; font-weight: bold">
        <span  style="color: white; font-size: 2.5rem; padding: 1rem;">{{ banner }}</span>
    </div>
    <div style="padding: 2.5rem; min-height: 550px;">
        <div style="display: flex;">
            <img id="avatar" src="{{user_avatar}}" />
            <div style="margin-left: 32px; margin-top: 32px">
                <span id="nickname">{{username}}</span>
                <span id="words">{{content}}</span>
            </div>
        </div>
    </div>
    <div id="footer">
        <span id="flh">{{foot_left_hint}}</span>
        <span id="frh">{{foot_right_hint}}</span>
    </div>

    <!-- 只显示图片的左上四分之一 -->
    <img id="bg-fixed-br" src="{{bg_fixed_br}}">

</body>

</html>

<script type="text/javascript">
    if (document.getElementById('title-bar').innerText.trim() === '') {
        document.getElementById('title-bar').style.display = 'none';
    }
</script>"""


class IdoknowAPIRender:

    ap: app.Application

    def __init__(self, ap: app.Application):
        self.ap = ap

    async def render(self, post: entity.Post) -> bytes:

        time_str = datetime.datetime.fromtimestamp(post.time_stamp).strftime("%Y-%m-%d %H:%M:%S")

        jinja_data = {
            "username": str(post.uin),
            "content": post.text,
            "user_avatar": f"https://q1.qlogo.cn/g?b=qq&amp;nk={post.uin}&amp;s=640",
            "foot_left_hint": f"{post.uin} 发表于 {time_str}",
            "foot_right_hint": "开发 @RockChinQ | @Soulter",
            "bg_fixed_br": f"https://q1.qlogo.cn/g?b=qq&amp;nk={self.ap.config.campux_qq_bot_uin}&amp;s=640",
            "banner": "",
        }

        if post.anon:
            jinja_data["username"] = "匿名"
            jinja_data["user_avatar"] = "https://avatars.githubusercontent.com/u/10137?v=4"
            jinja_data["foot_left_hint"] = "匿名用户 发表于 " + time_str

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.ap.config.campux_text_to_image_api+"/generate",
                json={
                    "tmpl": jinja_template,
                    "tmpldata": jinja_data,
                    "json": True,
                    "options": {
                        "full_page": True
                    }
                }
            ) as resp:
                resp_json = await resp.json()

                img = await session.get(
                    self.ap.config.campux_text_to_image_api+"/"+resp_json['data']['id']
                )

                return await img.read()
