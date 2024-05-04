import aiohttp
import nonebot

from . import errors
from ..common import entity


config = nonebot.get_driver().config


class CampuxAPI:
    def __init__(self):
        pass

    async def data(
        self,
        method: str,
        path: str,
        params: dict = {},
        body: dict = {},
    ) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                f"{config.campux_api}{path}",
                params=params,
                json=body,
                headers={"Authorization": f"Bearer {config.campux_token}"}
            ) as resp:
                return await self.assert_data(resp)

    async def read(
        self,
        method: str,
        path: str,
        params: dict = {},
        body: dict = {},
    ) -> bytes:
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                f"{config.campux_api}{path}",
                params=params,
                json=body,
                headers={"Authorization": f"Bearer {config.campux_token}"}
            ) as resp:
                return await resp.read()

    async def assert_data(self, resp: aiohttp.ClientResponse) -> dict:
        if resp.status != 200:
            raise errors.APIError(resp.status, await resp.text())

        obj = await resp.json()

        if obj["code"] != 0:
            raise errors.APIError(obj["code"], obj["msg"])

        return obj["data"]

    async def sign_up(self, uin: int) -> str:
        """/v1/account/create
        
        POST
        {
            "uin": 123456789
        }
        """
        data = await self.data(
            "POST",
            "/v1/account/create",
            body={"uin": uin}
        )

        return data["passwd"]
    
    async def reset_password(self, uin: int) -> str:
        """/v1/account/reset
        
        POST
        {
            "uin": 123456789
        }
        """
        data = await self.data(
            "PUT",
            "/v1/account/reset",
            body={"uin": uin}
        )

        return data["passwd"]

    async def get_post_info(self, post_id: int) -> entity.Post:
        """/v1/post/get-post-info/10
        
        GET
        """
        data = await self.data(
            "GET",
            f"/v1/post/get-post-info/{post_id}"
        )
        if data['post'] is None:
            return None

        return entity.Post(**data['post'])
    
    async def download_image(self, image_key: str) -> bytes:
        """/v1/post/download-image/{image-key}
        
        GET
        """
        return await self.read(
            "GET",
            f"/v1/post/download-image/{image_key}"
        )
    
    async def save_image_to_file(self, image_key: str, save_dir: str='.') -> str:
        """/v1/post/download-image/{image-key}
        
        GET
        """
        image = await self.download_image(image_key)

        whole_path = f"{save_dir}/{image_key}"
        with open(whole_path, "wb") as f:
            f.write(image)

        return whole_path
    
    async def review_post(self, post_id: int, option: str, comment: str):
        """/v1/post/review-post
        
        POST
        {
            "post_id": 1,
            "option": "approve",
            "comment": ""
        }
        """
        return await self.data(
            "POST",
            "/v1/post/review-post",
            body={
                "post_id": post_id,
                "option": option,
                "comment": comment
            }
        )
    
    async def post_post_log(
        self,
        post_id: int,
        op: int,
        old_stat: str,
        new_stat: str,
        comment: str
    ):
        """/v1/post/post-log
        
        POST
        {
            "post_id": 1,
            "op": 1,
            "old_stat": "pending_approval",
            "new_stat": "approved",
            "comment": ""
        }
        """
        return await self.data(
            "POST",
            "/v1/post/post-log",
            body={
                "post_id": post_id,
                "op": op,
                "old_stat": old_stat,
                "new_stat": new_stat,
                "comment": comment
            }
        )
        
campux_api = None

if campux_api is None:
    campux_api = CampuxAPI()
