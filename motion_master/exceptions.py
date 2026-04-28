from __future__ import annotations


class MotionMasterError(Exception):
    """Raised when the Motion Master API returns a non-2xx response."""

    def __init__(self, message: str, code: int | None = None, status_code: int | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code
