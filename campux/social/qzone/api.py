from __future__ import annotations

import asyncio
import json
import traceback

from nonebot import logger
import nonebot.adapters.onebot.v11.message as message
import requests

from ...core import app
from . import login


def generate_gtk(skey) -> str:
    """生成gtk"""
    hash_val = 5381
    for i in range(len(skey)):
        hash_val += (hash_val << 5) + ord(skey[i])
    return str(hash_val & 2147483647)

GET_VISITOR_AMOUNT_URL="https://h5.qzone.qq.com/proxy/domain/g.qzone.qq.com/cgi-bin/friendshow/cgi_get_visitor_more?uin={}&mask=7&g_tk={}&page=1&fupdate=1&clear=1"

class QzoneAPI:
    
    ap: app.Application

    cookies: dict

    gtk2: str

    uin: int

    def __init__(self, ap: app.Application, cookies_dict: dict={}):
        self.ap = ap
        self.cookies = cookies_dict
        self.gtk2 = ''
        self.uin = 0

        if 'qzone_cookies' in self.ap.cache.data and not cookies_dict and self.ap.cache.data['qzone_cookies']:
            self.cookies = self.ap.cache.data['qzone_cookies']

        if 'p_skey' in self.cookies:
            self.gtk2 = generate_gtk(self.cookies['p_skey'])

        if 'uin' in self.cookies:
            self.uin = int(self.cookies['uin'][1:])

    async def token_valid(self) -> bool:
        try:
            today, total = await self.get_visitor_amount()
            logger.info("检查cookies有效性结果：{}, {}".format(today, total))
            return True
        except Exception as e:
            traceback.print_exc()
            return False

    async def relogin(self):
        loginmgr = login.QzoneLogin()

        async def qrcode_callback(content: bytes):
            asyncio.create_task(self.ap.imbot.send_private_message(
                self.ap.config.campux_qq_admin_uin,
                message=[
                    message.MessageSegment.text("请使用QQ扫描以下二维码以登录QQ空间："),
                    message.MessageSegment.image(content)
                ]
            ))

        self.cookies = await loginmgr.login_via_qrcode(qrcode_callback)

        if 'p_skey' in self.cookies:
            self.gtk2 = generate_gtk(self.cookies['p_skey'])

        if 'uin' in self.cookies:
            self.uin = int(self.cookies['uin'][1:])

        asyncio.create_task(self.ap.imbot.send_private_message(
            self.ap.config.campux_qq_admin_uin,
            "登录流程完成。"
        ))

        self.ap.cache.data['qzone_cookies'] = self.cookies
        self.ap.cache.save()

    async def get_visitor_amount(self) -> tuple[int, int]:
        """获取空间访客信息
        
        Returns:
            tuple[int, int]: 今日访客数, 总访客数
        """
        res = requests.get(
            url=GET_VISITOR_AMOUNT_URL.format(self.uin, self.gtk2),
            cookies=self.cookies,
            timeout=10
        )
        json_text = res.text.replace("_Callback(", '')[:-3]

        try:
            json_obj = json.loads(json_text)
            visit_count = json_obj['data']
            return visit_count['todaycount'], visit_count['totalcount']
        except Exception as e:
            raise e
