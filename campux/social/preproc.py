from __future__ import annotations

import traceback
import re

from ..core import app
from ..common import entity


class PostPreprocessor:

    def __init__(self, ap: app.Application):
        self.ap = ap

    async def preprocess_post(self, post: entity.Post) -> entity.Post:
        """预处理稿件"""
        try:
            post.extra_text = await self.emotion_text_preprocess(post)
        except Exception as e:
            traceback.print_exc()
            post.extra_text = ''

        return post

    async def emotion_text_preprocess(self, post: entity.Post) -> str:
        """发表时的附带文本预处理"""

        text = post.text
        post_id = post.id
        uin = str(post.uin)

        def at(user_id):
            return f"@{{uin:{user_id},nick:,who:1}}"

        def links():
            # 从 text 中提取链接
            return re.findall(r'https?://[^\s]+', text)

        extra_raw_text = self.ap.meta.data['post_publish_text']

        extra_text = eval(extra_raw_text)

        # exec(extra_raw_text, locals())

        return extra_text