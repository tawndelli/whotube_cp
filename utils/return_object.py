class returnObject:
    message: str
    success: bool
    data: any
    status_code: int

    def __init__(self, message, success, data=None, status_code=200) -> None:
        self.message = message
        self.success = success
        self.data = data
        self.status_code = status_code