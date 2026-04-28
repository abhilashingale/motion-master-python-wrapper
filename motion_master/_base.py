from __future__ import annotations

from typing import Any

import requests

from .exceptions import MotionMasterError


class _BaseClient:
    """Shared HTTP machinery for System and Device."""

    def __init__(self, base_url: str = "http://localhost:63526/api") -> None:
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()

    def _build_params(self, **kwargs: Any) -> dict[str, Any]:
        """Filter None values and convert snake_case keys to kebab-case."""
        result: dict[str, Any] = {}
        for key, value in kwargs.items():
            if value is None:
                continue
            http_key = key.replace("_", "-")
            result[http_key] = str(value).lower() if isinstance(value, bool) else value
        return result

    def _handle_response(self, response: requests.Response) -> Any:
        if not response.ok:
            try:
                body = response.json()
                raise MotionMasterError(
                    message=body.get("message", response.text),
                    code=body.get("code"),
                    status_code=response.status_code,
                )
            except (ValueError, KeyError):
                raise MotionMasterError(message=response.text, status_code=response.status_code)

        if not response.content:
            return None
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return response.json()
        if "text/" in content_type:
            return response.text
        return response.content

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        return self._handle_response(self._session.get(url, params=params or {}))

    def _post(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        json: Any = None,
        data: bytes | None = None,
    ) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = {"Content-Type": "application/octet-stream"} if data is not None else {}
        return self._handle_response(
            self._session.post(url, params=params or {}, json=json, data=data, headers=headers)
        )

    def _put(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        json: Any = None,
        data: bytes | None = None,
    ) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = {"Content-Type": "application/octet-stream"} if data is not None else {}
        return self._handle_response(
            self._session.put(url, params=params or {}, json=json, data=data, headers=headers)
        )

    def _delete(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        return self._handle_response(self._session.delete(url, params=params or {}))
