"""
Read or write a single object-dictionary entry on one or more devices.

Usage
-----
    # Read 0x6064:00 from the device at EtherCAT position 3:
    pixi run python examples/read_write_object.py --device 3 --index 0x6064 --subindex 0x00

    # Write the value 37 to 0x6098:00 on devices at positions 1 and 2:
    pixi run python examples/read_write_object.py --devices 1 2 --index 0x6098 --subindex 0x00 --write 37

    # Read from all connected devices:
    pixi run python examples/read_write_object.py --index 0x1018 --subindex 0x01

    # Write and save to NVM (triggers Store Parameters 0x1010:01):
    pixi run python examples/read_write_object.py --devices 1 --index 0x6098 --subindex 0x00 --write 37 --save

Arguments
---------
--index       Object dictionary index in hex (e.g. 0x6064).  Required.
--subindex    Object dictionary subindex in hex (e.g. 0x00).  Required.
--write       Value to write.  Omit to perform a read instead.
--devices     EtherCAT chain position(s) to target (default: all connected devices).
--save        After a successful write, trigger NVM save (0x1010:01 = 'evas').
--url         Motion Master API base URL (default: http://localhost:63526/api).
"""

import argparse
import sys

from motion_master import MotionMasterError, System

STORE_PARAMS_INDEX    = "0x1010"
STORE_PARAMS_SUBINDEX = "0x01"
STORE_PARAMS_VALUE    = 0x65766173  # ASCII 'e','v','a','s'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read or write a single object-dictionary entry on one or more devices."
    )
    parser.add_argument("--index", required=True,
                        help="Object dictionary index in hex (e.g. 0x6064)")
    parser.add_argument("--subindex", required=True,
                        help="Object dictionary subindex in hex (e.g. 0x00)")
    parser.add_argument("--write", metavar="VALUE",
                        help="Value to write. Omit to read instead.")
    parser.add_argument("--devices", type=int, nargs="+", metavar="POS",
                        help="EtherCAT chain position(s) to target (default: all connected devices)")
    parser.add_argument("--save", action="store_true",
                        help="After a successful write, save parameters to NVM (0x1010:01)")
    parser.add_argument("--url", default="http://localhost:63526/api",
                        help="Motion Master API base URL")
    return parser.parse_args()


def read_object(device, index: str, subindex: str) -> bool:
    try:
        result = device.upload_parameter(index, subindex)
        value = result.get("value", result) if isinstance(result, dict) else result
        print(f"  {index}:{subindex} = {value}")
        return True
    except MotionMasterError as exc:
        print(f"  ERROR reading {index}:{subindex}: {exc}", file=sys.stderr)
        return False


def write_object(device, index: str, subindex: str, raw_value: str, save: bool) -> bool:
    # Try to coerce the value to int (hex or decimal); fall back to string.
    try:
        value: int | str = int(raw_value, 0)
    except ValueError:
        value = raw_value

    try:
        device.download_parameter(index, subindex, value)
        print(f"  {index}:{subindex} written: {value}")
    except MotionMasterError as exc:
        print(f"  ERROR writing {index}:{subindex}: {exc}", file=sys.stderr)
        return False

    # Read back to confirm.
    try:
        result = device.upload_parameter(index, subindex)
        readback = result.get("value", result) if isinstance(result, dict) else result
        print(f"  read-back: {readback}")
    except MotionMasterError as exc:
        print(f"  WARNING: could not read back {index}:{subindex}: {exc}", file=sys.stderr)

    if save:
        try:
            device.download_parameter(STORE_PARAMS_INDEX, STORE_PARAMS_SUBINDEX, STORE_PARAMS_VALUE)
            print("  Parameters saved to NVM.")
        except MotionMasterError as exc:
            print(f"  ERROR saving parameters to NVM: {exc}", file=sys.stderr)
            return False

    return True


def main() -> None:
    args = parse_args()

    system = System(args.url)
    try:
        system.connect()
        print(f"Connected to Motion Master at {args.url}\n")

        if args.devices:
            targets = [(pos, f"EtherCAT position {pos}") for pos in args.devices]
        else:
            all_devices = system.get_devices()
            if not all_devices:
                print("No devices found.")
                return
            targets = [
                (dev.get("deviceAddress") or dev.get("serialNumber"),
                 f"EtherCAT position {dev.get('deviceAddress', 'unknown')}")
                for dev in all_devices
            ]

        mode = f"write {args.write}" if args.write is not None else "read"
        print(f"Operation : {mode}")
        print(f"Object    : {args.index}:{args.subindex}")
        print(f"Devices   : {len(targets)}\n")

        failed: list[str] = []

        for ref, label in targets:
            print(f"Device {label}:")
            device = system.device(ref)

            if args.write is not None:
                ok = write_object(device, args.index, args.subindex, args.write, args.save)
            else:
                ok = read_object(device, args.index, args.subindex)

            if not ok:
                failed.append(label)
            print()

    finally:
        system.disconnect()
        print("Disconnected.")

    total = len(targets) if "targets" in dir() else 0
    succeeded = total - len(failed)
    print(f"Done. {succeeded}/{total} device(s) {'written' if args.write is not None else 'read'} successfully.")

    if failed:
        print(f"Failed: {failed}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
