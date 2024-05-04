from __future__ import annotations

import os
import uuid
import json

from dify_client import AsyncClient, models

from ..core import app
from ..common import entity


class ReviewAgent:

    dify: AsyncClient

    ap: app.Application

    uuid: str

    def __init__(self, ap: app.Application):
        self.ap = ap

        self.dify = AsyncClient(
            api_key=self.ap.config.dify_api_key,
            api_base=self.ap.config.dify_api_base
        )

        self.uuid = str(uuid.uuid4())

    async def get_ai_review(self, post: entity.Post) -> dict:

        inputs = {
            "text": post.text,
            "anon": f"{'true' if post.anon else 'false'}",
            "uin": post.uin,
        }

        files: list[models.File] = []

        if post.images:

            for img in post.images:
                files.append(
                    models.File(
                        type=models.base.FileType.IMAGE,
                        transfer_method="local_file",
                        upload_file_id=(await self.dify.aupload_files(
                            file=self.ap.imbot.image_to_base64(await self.ap.cpx_api.download_image(img)),
                            req=models.UploadFileRequest(
                                user=self.uuid,
                            )
                        )).id
                    )
                )

        print(files)

        gen = await self.dify.arun_workflows(
            req=models.WorkflowsRunRequest(
                inputs=inputs,
                response_mode=models.ResponseMode.STREAMING,
                files=files,
                user=self.uuid
            ),
            timeout=60
        )

        payload = None

        async for msg in gen:
            # print(msg)

            if msg.event == models.StreamEvent.NODE_FINISHED:
                payload = msg.data

        return json.loads(payload.inputs['result'])
