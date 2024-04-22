import aiohttp
import nonebot

from . import errors


config = nonebot.get_driver().config


class CampuxAPI:
    def __init__(self):
        pass

    async def do(
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
                data = await self.assert_data(resp)
                return data

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
        data = await self.do(
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
        data = await self.do(
            "PUT",
            "/v1/account/reset",
            body={"uin": uin}
        )

        return data["passwd"]
        
campux_api = None

if campux_api is None:
    campux_api = CampuxAPI()
