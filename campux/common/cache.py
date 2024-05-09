from __future__ import annotations

import os
import sys
import json


class CacheManager:

    data: dict

    file: str

    def __init__(self, file: str="data/cache.json"):
        self.data = {}
        self.file = file

        if not os.path.exists(file):
            with open(file, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def load(self):
        with open(self.file, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def save(self):
        with open(self.file, "w", encoding="utf-8") as f:
            json.dump(self.data, f)
