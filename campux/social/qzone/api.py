from __future__ import annotations

import asyncio
import json
import base64
import traceback

import requests

from ...core import app
from . import login


def generate_gtk(skey) -> str:
    """生成gtk"""
    hash_val = 5381
    for i in range(len(skey)):
        hash_val += (hash_val << 5) + ord(skey[i])
    return str(hash_val & 2147483647)


def get_picbo_and_richval(upload_result):
    json_data = upload_result

    # for debug
    if 'ret' not in json_data:
        raise Exception("获取图片picbo和richval失败")
    # end

    if json_data['ret'] != 0:
        raise Exception("上传图片失败")
    picbo_spt = json_data['data']['url'].split('&bo=')
    if len(picbo_spt) < 2:
        raise Exception("上传图片失败")
    picbo = picbo_spt[1]

    richval = ",{},{},{},{},{},{},,{},{}".format(json_data['data']['albumid'], json_data['data']['lloc'],
                                                 json_data['data']['sloc'], json_data['data']['type'],
                                                 json_data['data']['height'], json_data['data']['width'],
                                                 json_data['data']['height'], json_data['data']['width'])

    return picbo, richval

GET_VISITOR_AMOUNT_URL="https://h5.qzone.qq.com/proxy/domain/g.qzone.qq.com/cgi-bin/friendshow/cgi_get_visitor_more?uin={}&mask=7&g_tk={}&page=1&fupdate=1&clear=1"
UPLOAD_IMAGE_URL="https://up.qzone.qq.com/cgi-bin/upload/cgi_upload_image"
EMOTION_PUBLISH_URL="https://user.qzone.qq.com/proxy/domain/taotao.qzone.qq.com/cgi-bin/emotion_cgi_publish_v6"

class QzoneAPI:
    
    ap: app.Application

    cookies: dict

    gtk2: str

    uin: int

    def get_account_id(self) -> int:
        return self.uin

    async def do(
        self,
        method: str,
        url: str,
        params: dict={},
        data: dict={},
        headers: dict={},
        cookies: dict=None,
        timeout: int=10
    ) -> requests.Response:

        if cookies is None:
            cookies = self.cookies
        
        return requests.request(
            method=method,
            url=url,
            params=params,
            data=data,
            headers=headers,
            cookies=cookies,
            timeout=timeout
        )

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

    async def token_valid(self, retry=3) -> bool:

        for i in range(retry):
            try:
                # 尝试从缓存加载cookies
                self.ap.cache.load()
                self.cookies = self.ap.cache.data['qzone_cookies']

                today, total = await self.get_visitor_amount()
                return True
            except Exception as e:
                traceback.print_exc()
                if i == retry - 1:
                    return False

    def image_to_base64(self, image: bytes) -> str:
        pic_base64 = base64.b64encode(image)

        return str(pic_base64)[2:-1]

    async def relogin(self, callback: callable):
        loginmgr = login.QzoneLogin()

        self.cookies = await loginmgr.login_via_qrcode(callback)

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
        res = await self.do(
            method="GET",
            url=GET_VISITOR_AMOUNT_URL.format(self.uin, self.gtk2),
        )
        json_text = res.text.replace("_Callback(", '')[:-3]

        try:
            json_obj = json.loads(json_text)
            visit_count = json_obj['data']
            return visit_count['todaycount'], visit_count['totalcount']
        except Exception as e:
            raise e

    async def upload_image(self, image: bytes) -> str:
        """上传图片"""

        res = await self.do(
            method="POST",
            url=UPLOAD_IMAGE_URL,
            data={
                "filename": "filename",
                "zzpanelkey": "",
                "uploadtype": "1",
                "albumtype": "7",
                "exttype": "0",
                "skey": self.cookies["skey"],
                "zzpaneluin": self.uin,
                "p_uin": self.uin,
                "uin": self.uin,
                "p_skey": self.cookies['p_skey'],
                "output_type": "json",
                "qzonetoken": "",
                "refer": "shuoshuo",
                "charset": "utf-8",
                "output_charset": "utf-8",
                "upload_hd": "1",
                "hd_width": "2048",
                "hd_height": "10000",
                "hd_quality": "96",
                "backUrls": "http://upbak.photo.qzone.qq.com/cgi-bin/upload/cgi_upload_image,http://119.147.64.75/cgi-bin/upload/cgi_upload_image",
                "url": "https://up.qzone.qq.com/cgi-bin/upload/cgi_upload_image?g_tk=" + self.gtk2,
                "base64": "1",
                "picfile": self.image_to_base64(image),
            },
            headers={
                'referer': 'https://user.qzone.qq.com/' + str(self.uin),
                'origin': 'https://user.qzone.qq.com'
            },
            timeout=60
        )
        if res.status_code == 200:
            return eval(res.text[res.text.find('{'):res.text.rfind('}') + 1])
        else:
            raise Exception("上传图片失败")

    async def publish_emotion(self, content: str, images: list[bytes]=[]) -> str:
        """发表说说
        :return: 说说tid
        :except: 发表失败
        """

        if images is None:
            images = []

        post_data = {

            "syn_tweet_verson": "1",
            "paramstr": "1",
            "who": "1",
            "con": content,
            "feedversion": "1",
            "ver": "1",
            "ugc_right": "1",
            "to_sign": "0",
            "hostuin": self.uin,
            "code_version": "1",
            "format": "json",
            "qzreferrer": "https://user.qzone.qq.com/" + str(self.uin)
        }

        if len(images) > 0:

            # 挨个上传图片
            pic_bos = []
            richvals = []
            for img in images:
                uploadresult = await self.upload_image(img)
                picbo, richval = get_picbo_and_richval(uploadresult)
                pic_bos.append(picbo)
                richvals.append(richval)

            post_data['pic_bo'] = ','.join(pic_bos)
            post_data['richtype'] = '1'
            post_data['richval'] = '\t'.join(richvals)

        res = await self.do(
            method="POST",
            url=EMOTION_PUBLISH_URL,
            params={
                'g_tk': self.gtk2,
                'uin': self.uin,
            },
            data=post_data,
            headers={
                'referer': 'https://user.qzone.qq.com/' + str(self.uin),
                'origin': 'https://user.qzone.qq.com'
            }
        )
        if res.status_code == 200:
            return res.json()['tid']
        else:
            raise Exception("发表说说失败: " + res.text)
