import asyncio
import os

import nonebot
# 初始化 NoneBot
nonebot.init()

from campux.core import app


async def main():

    if not os.path.exists("data/"):
        os.mkdir("data/")

    ap = await app.create_app()

    from campux.imbot import nbmod
    nbmod.ap = ap

    await ap.run()


if __name__ == "__main__":
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()
