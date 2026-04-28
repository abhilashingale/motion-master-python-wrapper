# motion-master-python-wrapper

A Python wrapper for the [Motion Master HTTP API](https://synapticon.github.io/oblac/motion-master-api/). Covers all endpoints in the API and organises them into two classes that mirror the API's tag hierarchy:

- **`System`** — connection management, version queries, device listing, and multi-device parameter operations.
- **`Device`** — per-device parameters, files, firmware, motion control, tuning, encoders, SMM, and monitoring.

## Installation

### With Pixi (recommended)

[Pixi](https://pixi.sh) manages the environment and dependencies automatically.

```bash
# Install pixi (once, system-wide)
# Windows
winget install prefix-dev.pixi
# macOS / Linux
curl -fsSL https://pixi.sh/install.sh | sh

# Clone and set up
git clone <repo-url>
cd motion-master-python-wrapper
pixi install
```

The default environment includes the package (editable) and `pytest`.

Common pixi commands:

```bash
pixi install          # create/update the environment from pixi.lock
pixi run python       # run Python inside the environment
pixi run pytest       # run tests
pixi shell            # drop into an activated shell
```

### With pip

```bash
pip install requests>=2.28.0
pip install -e .      # editable install of this package
```

**Requirements:** Python 3.10+

## Architecture

```
motion_master/
├── __init__.py       # exports System, Device, MotionMasterError
├── _base.py          # shared HTTP session (requests.Session), response handling
├── system.py         # System class — 9 methods + device() factory
├── device.py         # Device class — 57 methods across 17 functional groups
└── exceptions.py     # MotionMasterError
```

`System.device(ref)` returns a `Device` that **shares the same HTTP session**, so you only pay for one TCP connection regardless of how many drives you talk to.

## Quickstart

### Option A — via System (recommended)

```python
from motion_master import System

system = System("http://localhost:63526/api")
system.connect()

devices = system.get_devices()
print(devices)  # list of connected drives with hardware info

drive = system.device(1)          # by EtherCAT chain position
# drive = system.device("8504-03-0002369-2329")  # or by serial number

system.disconnect()
```

### Option B — Device standalone

```python
from motion_master import Device

drive = Device(device_ref=1, base_url="http://localhost:63526/api")
```

## Reading and writing parameters

Parameters are addressed by CANopen **index** and **subindex** strings (e.g. `"0x6064"`, `"0x00"`).

### Read a single parameter (SDO upload)

```python
from motion_master import System

system = System("http://localhost:63526/api")
system.connect()
drive = system.device(1)

# Read actual position (0x6064:00)
result = drive.upload_parameter("0x6064", "0x00")
print(result)
# {'value': 12345, 'unit': 'inc', ...}

system.disconnect()
```

### Write a single parameter (SDO download)

```python
from motion_master import System

system = System("http://localhost:63526/api")
system.connect()
drive = system.device(1)

# Set target position (0x607A:00) to 10 000 increments
drive.download_parameter("0x607A", "0x00", 10000)

# Persist changes to config.csv on the device
drive.save_config()

system.disconnect()
```

### Read multiple parameters in one call

```python
result = drive.get_parameter_values([
    {"index": "0x6064", "subindex": "0x00"},  # actual position
    {"index": "0x606C", "subindex": "0x00"},  # actual velocity
])
print(result)
```

### Write multiple parameters in one call

```python
drive.set_parameter_values([
    {"index": "0x607A", "subindex": "0x00", "value": 10000},  # target position
    {"index": "0x6081", "subindex": "0x00", "value": 500},    # profile velocity
])
drive.save_config()
```

### Read all parameters at once

```python
all_params = drive.get_parameters()
```

## Error handling

All non-2xx responses raise `MotionMasterError`:

```python
from motion_master import System, MotionMasterError

system = System("http://localhost:63526/api")
try:
    system.connect()
    drive = system.device(1)
    drive.upload_parameter("0x6064", "0x00")
except MotionMasterError as e:
    print(f"API error {e.status_code}: {e}")
finally:
    system.disconnect()
```

## Full method reference

### System

| Method | Description |
|---|---|
| `connect(hostname, request_timeout)` | Connect to Motion Master (defaults to localhost) |
| `disconnect()` | Close WebSocket connections |
| `get_version()` | Motion Master Client library version |
| `get_system_version(request_timeout)` | Connected Motion Master process version |
| `get_system_log(request_timeout)` | System log content and run environment |
| `set_system_client_timeout(timeout)` | Client idle timeout in milliseconds |
| `get_devices(request_timeout)` | List connected devices |
| `get_multi_device_parameter_values(requests_body, ...)` | Batch parameter read across multiple devices |
| `set_multi_device_parameter_values(parameter_values, ...)` | Batch parameter write across multiple devices |
| `device(device_ref)` | Return a Device sharing this session |

### Device

| Group | Methods |
|---|---|
| **Parameters** | `get_parameter_info`, `upload_parameter`, `download_parameter`, `download_binary_parameter`, `get_parameter_values`, `set_parameter_values`, `get_parameters` |
| **Files** | `get_file_list`, `unlock_protected_files`, `get_file`, `set_file`, `delete_file`, `get_log`, `save_config`, `load_config` |
| **Firmware** | `start_firmware_installation`, `factory_reset` |
| **Motion control** | `quick_stop`, `reset_fault`, `set_modes_of_operation`, `transition_to_cia402_state`, `get_cia402_state`, `set_halt_bit`, `apply_set_point`, `force_on_demand_parameters_update` |
| **Motion controller** | `set_motion_controller_parameters`, `enable_motion_controller`, `disable_motion_controller` |
| **EtherCAT** | `get_ethercat_network_state`, `set_ethercat_network_state` |
| **System ID & auto-tuning** | `start_system_identification`, `compute_auto_tuning_gains_velocity`, `compute_auto_tuning_gains_position`, `start_full_auto_tuning_velocity`, `start_full_auto_tuning_position`, `stop_full_auto_tuning` |
| **Motion profiles** | `run_torque_profile`, `run_velocity_profile`, `run_position_profile` |
| **Open-loop & chirp** | `start_open_loop_field_control`, `run_chirp_signal`, `start_limited_range_system_identification` |
| **Offset detection** | `start_offset_detection`, `run_offset_detection` |
| **Cogging torque** | `start_cogging_torque_recording`, `get_cogging_torque_data` |
| **Circulo encoder** | `get_circulo_encoder_magnet_distance`, `start_circulo_encoder_narrow_angle_calibration`, `start_circulo_encoder_configuration`, `check_circulo_encoder_errors`, `write_circulo_integrated_encoder_config_bin_file` |
| **Integro encoder** | `start_integro_encoder_calibration`, `get_integro_encoder_firmware_version`, `readout_integro_integrated_encoder_error` |
| **Kubler encoder** | `run_kubler_encoder_register_communication_os_command`, `reset_kubler_encoder_multiturn_position` |
| **OS commands** | `run_os_command` |
| **SMM** | `configure_smm`, `update_smm_software`, `update_smm_software_to_encrypted` |
| **Monitoring** | `start_monitoring`, `get_monitoring_data`, `stop_monitoring` |
