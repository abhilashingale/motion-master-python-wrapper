"""
Motion Master HTTP API — Python wrapper
========================================

Two entry points are provided, matching the API's tag hierarchy:

  System  — connection management, version queries, device listing, multi-device ops
  Device  — per-device parameters, files, motion control, tuning, encoders, SMM, monitoring

Quickstart
----------
Option A — via System (recommended, shares one HTTP session):

    from motion_master import System

    system = System("http://localhost:63526/api")
    system.connect()

    devices = system.get_devices()
    drive = system.device(1)              # or system.device("8504-03-0002369-2329")

    position = drive.upload_parameter("0x6064", "0x00")
    drive.download_parameter("0x607A", "0x00", 10000)
    drive.save_config()

    system.disconnect()

Option B — Device standalone (creates its own HTTP session):

    from motion_master import Device

    drive = Device(device_ref=1, base_url="http://localhost:63526/api")
    position = drive.upload_parameter("0x6064", "0x00")

Architecture note
-----------------
If you use System and Device independently (Option B), each creates its
own requests.Session.  Prefer Option A (system.device(ref)) when you need
both system-level and device-level calls in the same script — it ensures a
single session and consistent base URL.

For large automation scripts that manage many drives, consider wrapping
System in a context manager or helper that calls connect/disconnect for you.
"""

from .device import Device
from .exceptions import MotionMasterError
from .system import System

__all__ = ["System", "Device", "MotionMasterError"]
