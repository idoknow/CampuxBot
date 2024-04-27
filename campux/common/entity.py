from __future__ import annotations

import pydantic


class Post(pydantic.BaseModel):
    """稿件
    
    {
        "id": 10,
        "uuid": "009",
        "uin": 1010553892,
        "text": "xxxx",
        "images": [],
        "anon": false,
        "status": "in_queue",
        "created_at": "2024-04-12T06:11:26.209Z"
    }
    """

    id: int
    """稿件ID"""

    uuid: str
    """稿件UUID"""

    uin: int
    """用户ID"""

    text: str
    """文本内容"""

    images: list[str]
    """图片key列表"""

    anon: bool
    """是否匿名"""

    status: str
    """状态"""

    created_at: str
    """创建时间"""

    time_stamp: int
    """时间戳"""
