from __future__ import annotations

from ..core import app


class RedisStreamMQ:

    ap: app.Application

    def __init__(self, ap: app.Application):
        self.ap = ap

    