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

        return entity.Post(**data['post'])
    
    async def download_image(self, image_key: str) -> bytes:
        """/v1/post/download-image/{image-key}
        
        GET
        """
        return await self.read(
            "GET",
            f"/v1/post/download-image/{image_key}"
        )
        
campux_api = None

if campux_api is None:
    campux_api = CampuxAPI()