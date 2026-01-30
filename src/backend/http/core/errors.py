from dataclasses import dataclass


@dataclass(frozen=True)
class AppError(Exception):
    message: str
    status_code: int = 400

    def __str__(self) -> str:
        return self.message


class BadRequestError(AppError):
    def __init__(self, message: str):
        super().__init__(message=message, status_code=400)


class NotFoundError(AppError):
    def __init__(self, message: str):
        super().__init__(message=message, status_code=404)


class UpstreamError(AppError):
    def __init__(self, message: str):
        super().__init__(message=message, status_code=502)

