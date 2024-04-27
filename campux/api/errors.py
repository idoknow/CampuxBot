
class APIError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message

    def __str__(self):
        return f"操作失败: {self.message}"