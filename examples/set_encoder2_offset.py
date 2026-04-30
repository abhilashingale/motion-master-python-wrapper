"""
Set the encoder-2 single-turn offset for all connected devices.

For each device:
  1. Read encoder-2 raw position
  2. Calculate the mid-range single-turn offset:
       if raw < 2^19 / 2:  offset = raw + 2^19
       else:                offset = raw - 2^19
  3. Write the offset to the device
  4. Set "Restore Home Position when loading configuration" to YES (1)
  5. Save configuration to flash

Usage
-----
    pixi run python examples/set_encoder2_offset.py
    pixi run python examples/set_encoder2_offset.py --url http://192.168.1.100:63526/api

    # Dry run — print calculated offsets without writing anything:
    pixi run python examples/set_encoder2_offset.py --dry-run

    # Read and display current offsets only:
    pixi run python examples/set_encoder2_offset.py --read-offsets

    # Clear (zero) the offset on all devices:
    pixi run python examples/set_encoder2_offset.py --clear-offsets

    # Target only devices at EtherCAT positions 3, 5 and 7:
    pixi run python examples/set_encoder2_offset.py --devices 3 5 7
"""

import argparse
import sys

from motion_master import MotionMasterError, System

# ---------------------------------------------------------------------------
# Object addresses — verify these against your firmware's object dictionary
# ---------------------------------------------------------------------------

ENC2_RAW_INDEX       = "0x2113"   # TODO: encoder-2 raw position actual value index
ENC2_RAW_SUBINDEX    = "0x2"     # TODO: adjust subindex if needed

ENC2_OFFSET_INDEX    = "0x2112"   # TODO: encoder-2 single-turn offset index
ENC2_OFFSET_SUBINDEX = "0x6"     # TODO: adjust subindex if needed

RESTORE_HOME_INDEX    = "0x2005"  # TODO: "Restore Home Position when loading config" index
RESTORE_HOME_SUBINDEX = "0x2"    # TODO: adjust subindex if needed

ENCODER_RESOLUTION = 1 << 20     # 1 048 576 counts per revolution (2^20)

# Store parameters object — write 'evas' ('save' backwards) to trigger NVM save
STORE_PARAMS_INDEX    = "0x1010"
STORE_PARAMS_SUBINDEX = "0x01"
STORE_PARAMS_VALUE    = 0x65766173  # ASCII 'e','v','a','s'


# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Set encoder-2 single-turn offset for all connected devices."
    )
    parser.add_argument("--url", default="http://localhost:63526/api",
                        help="Motion Master API base URL")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print calculated offsets without writing to devices")
    parser.add_argument("--read-offsets", action="store_true",
                        help="Read and display the current single-turn offset on each device, then exit")
    parser.add_argument("--clear-offsets", action="store_true",
                        help="Reset the single-turn offset to 0 on all devices and save config")
    parser.add_argument("--devices", type=int, nargs="+", metavar="POS",
                        help="EtherCAT chain position(s) to target (default: all connected devices)")
    return parser.parse_args()


def store_parameters(device) -> bool:
    """Trigger NVM save by writing 0x65766173 ('evas') to Store Parameters (0x1010:01)."""
    try:
        device.download_parameter(STORE_PARAMS_INDEX, STORE_PARAMS_SUBINDEX, STORE_PARAMS_VALUE)
        print("  Parameters stored to NVM.")
        return True
    except MotionMasterError as exc:
        print(f"  ERROR storing parameters: {exc}", file=sys.stderr)
        return False


def clear_offset(device) -> bool:
    """Write 0 to the single-turn offset and save config."""
    try:
        device.download_parameter(ENC2_OFFSET_INDEX, ENC2_OFFSET_SUBINDEX, 0)
        print("  single-turn offset cleared (set to 0).")
    except MotionMasterError as exc:
        print(f"  ERROR clearing offset: {exc}", file=sys.stderr)
        return False

    return store_parameters(device)


def read_current_offset(device) -> bool:
    """Read and print the current single-turn offset stored on the device."""
    try:
        result = device.upload_parameter(ENC2_OFFSET_INDEX, ENC2_OFFSET_SUBINDEX)
        current = result.get("value", result) if isinstance(result, dict) else result
        print(f"  current single-turn offset = {current}")
        return True
    except MotionMasterError as exc:
        print(f"  ERROR reading offset: {exc}", file=sys.stderr)
        return False


def calculate_offset(raw: int) -> int:
    half = ENCODER_RESOLUTION // 2
    if raw < half:
        return raw + half
    else:
        return raw - half


def process_device(device, label: str, dry_run: bool) -> bool:
    """Read encoder-2 raw position, calculate offset, and write it back.

    Returns True on success, False on failure.
    """
    try:
        result = device.upload_parameter(ENC2_RAW_INDEX, ENC2_RAW_SUBINDEX)
        raw = result.get("value", result) if isinstance(result, dict) else result
        raw = int(raw)
    except MotionMasterError as exc:
        print(f"  ERROR reading encoder-2 raw position: {exc}", file=sys.stderr)
        return False

    print(f"  encoder-2 raw = {raw}")
    offset = calculate_offset(raw)
    print(f"  calculated offset = {offset}"
          f"  ({'raw < half' if raw < ENCODER_RESOLUTION // 2 else 'raw >= half'})")

    if dry_run:
        print("  [dry-run] skipping write.")
        return True

    try:
        device.download_parameter(ENC2_OFFSET_INDEX, ENC2_OFFSET_SUBINDEX, offset)
    except MotionMasterError as exc:
        print(f"  ERROR writing single-turn offset: {exc}", file=sys.stderr)
        return False

    try:
        result = device.upload_parameter(ENC2_OFFSET_INDEX, ENC2_OFFSET_SUBINDEX)
        readback = result.get("value", result) if isinstance(result, dict) else result
        print(f"  offset read-back = {readback}")
    except MotionMasterError as exc:
        print(f"  ERROR reading back offset: {exc}", file=sys.stderr)
        return False

    try:
        device.download_parameter(RESTORE_HOME_INDEX, RESTORE_HOME_SUBINDEX, 1)
    except MotionMasterError as exc:
        print(f"  ERROR setting Restore Home Position: {exc}", file=sys.stderr)
        return False

    if not store_parameters(device):
        return False

    try:
        result = device.upload_parameter(ENC2_RAW_INDEX, ENC2_RAW_SUBINDEX)
        raw_after = result.get("value", result) if isinstance(result, dict) else result
        print(f"  encoder-2 raw after offset = {raw_after}")
    except MotionMasterError as exc:
        print(f"  ERROR reading encoder-2 raw after offset: {exc}", file=sys.stderr)
        return False

    return True


def main() -> None:
    args = parse_args()

    if args.dry_run:
        print("[dry-run mode — no parameters will be written]\n")

    system = System(args.url)
    try:
        system.connect()
        print(f"Connected to Motion Master at {args.url}\n")

        if args.devices:
            targets = [(pos, f"position {pos}") for pos in args.devices]
        else:
            all_devices = system.get_devices()
            if not all_devices:
                print("No devices found.")
                return
            targets = [
                (dev.get("deviceAddress") or dev.get("serialNumber"),
                 dev.get("serialNumber", str(dev.get("deviceAddress"))))
                for dev in all_devices
            ]

        print(f"Targeting {len(targets)} device(s).\n")

        failed: list[str] = []

        for ref, label in targets:
            print(f"Device {label}:")

            drive = system.device(ref)

            if args.read_offsets:
                ok = read_current_offset(drive)
            elif args.clear_offsets:
                ok = clear_offset(drive)
            else:
                ok = process_device(drive, label, dry_run=args.dry_run)

            if not ok:
                failed.append(label)

            print()

    finally:
        system.disconnect()
        print("Disconnected.")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    total = len(targets) if "targets" in dir() else 0
    succeeded = total - len(failed)
    print(f"Done. {succeeded}/{total} device(s) updated successfully.")

    if failed:
        print(f"Failed: {failed}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
