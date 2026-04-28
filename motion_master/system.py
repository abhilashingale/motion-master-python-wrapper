from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ._base import _BaseClient

if TYPE_CHECKING:
    from .device import Device


class System(_BaseClient):
    """System-level calls not specific to a single device.

    Covers: connect/disconnect, version queries, device listing,
    and multi-device parameter operations.

    Usage::

        system = System("http://localhost:63526/api")
        system.connect()
        devices = system.get_devices()
        drive = system.device(1)   # returns a Device sharing this session
        drive.upload_parameter("0x6064", "0x00")
        system.disconnect()
    """

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def connect(self, hostname: str | None = None, request_timeout: int | None = None) -> dict:
        """Connect to Motion Master; omit hostname to use localhost."""
        path = f"connect/{hostname}" if hostname else "connect"
        return self._get(path, self._build_params(request_timeout=request_timeout))

    def disconnect(self) -> None:
        """Close WebSocket connections and destroy the client object."""
        self._get("disconnect")

    # ------------------------------------------------------------------
    # Version
    # ------------------------------------------------------------------

    def get_version(self) -> dict:
        """Return the Motion Master Client library version from package.json."""
        return self._get("version")

    def get_system_version(self, request_timeout: int | None = None) -> dict:
        """Return the version of the connected Motion Master process."""
        return self._get("system-version", self._build_params(request_timeout=request_timeout))

    # ------------------------------------------------------------------
    # System info
    # ------------------------------------------------------------------

    def get_system_log(self, request_timeout: int | None = None) -> dict:
        """Retrieve the system log (content + runEnv)."""
        return self._get("system-log", self._build_params(request_timeout=request_timeout))

    def set_system_client_timeout(self, timeout: int) -> None:
        """Set how long (ms) Motion Master waits before considering the client gone."""
        self._get(f"set-system-client-timeout/{timeout}")

    # ------------------------------------------------------------------
    # Devices
    # ------------------------------------------------------------------

    def get_devices(self, request_timeout: int | None = None) -> list:
        """Return a list of connected devices with hardware descriptions."""
        return self._get("devices", self._build_params(request_timeout=request_timeout))

    # ------------------------------------------------------------------
    # Multi-device parameter operations
    # ------------------------------------------------------------------

    def get_multi_device_parameter_values(
        self,
        requests_body: list[dict[str, Any]],
        load_from_cache: bool | None = None,
        request_timeout: int | None = None,
    ) -> dict:
        """Retrieve parameter values for multiple devices in one call."""
        return self._post(
            "devices/get-multi-device-parameter-values",
            params=self._build_params(load_from_cache=load_from_cache, request_timeout=request_timeout),
            json=requests_body,
        )

    def set_multi_device_parameter_values(
        self,
        parameter_values: list[dict[str, Any]],
        request_timeout: int | None = None,
    ) -> dict:
        """Set parameter values for multiple devices in one call."""
        return self._post(
            "devices/set-multi-device-parameter-values",
            params=self._build_params(request_timeout=request_timeout),
            json=parameter_values,
        )

    # ------------------------------------------------------------------
    # Device factory — shares this session and base URL
    # ------------------------------------------------------------------

    def device(self, device_ref: str | int) -> "Device":
        """Return a Device instance that shares this HTTP session.

        device_ref can be a position (int), device address (int), or
        serial number (str) such as "8504-03-0002369-2329".
        """
        from .device import Device  # local import to avoid circular dependency

        d = Device.__new__(Device)
        d.base_url = self.base_url
        d._session = self._session
        d.device_ref = str(device_ref)
        return d
