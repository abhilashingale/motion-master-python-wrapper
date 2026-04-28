"""
Copy SMM configuration from one device to one or more target devices.

The script reads all writable SMM safe-objects from the source device,
builds a temporary CSV, and pushes it to each target via configure_smm().

Skipped (read-only / status / PDO / SyncManager objects):
  - Real-time data: 0x6611, 0x6613, 0x6621, 0x6760, 0x6770
  - Commands:       0x6630, 0x6632, 0x6640, 0x6641, 0x6650, 0x6660,
                    0x6668, 0x6670, 0x6690
  - Manufacturing:  0x2610, 0x2611
  - Monitoring:     0x2600–0x2605, 0x6502, 0x2701–0x2705
  - PDO/SyncMgr:    0x1700–0x1C33, 0xF000, 0xF030, 0xF050

Usage
-----
    pixi run python examples/copy_smm_config.py --source 3 --targets 27 28 29

    # Save the generated CSV for inspection:
    pixi run python examples/copy_smm_config.py --source 3 --targets 27 28 \\
        --save smm_snapshot.csv

    # Skip FSoE address objects (each device keeps its own address):
    pixi run python examples/copy_smm_config.py --source 3 --targets 27 28 \\
        --skip-address

Arguments
---------
--source        EtherCAT chain position of the source device (1-based).
--targets       One or more EtherCAT chain positions to copy the config to.
--url           Motion Master API base URL (default: http://localhost:63526/api).
--username      SMM username (default: Test).
--password      SMM password (default: SomanetSMM).
--save          Optional path to save the generated CSV for inspection.
--skip-address  Exclude the Safe address object (0x2620:03) so each target
                keeps its own address.
"""

import argparse
import csv
import io
import sys

from motion_master import MotionMasterError, System

# ---------------------------------------------------------------------------
# Configurable SMM safe-objects
# (index, subindex, description)
# Excludes read-only, status, command, PDO, and SyncManager objects.
# ---------------------------------------------------------------------------

SMM_OBJECTS: list[tuple[str, str, str]] = [
    # NOTE: FSoE network communication objects (0xF980:01, 0xE901:02/04/06) are
    # intentionally excluded — they are EtherCAT-layer config, not part of the
    # SMM parameter structure validated by configure_smm().

    # General safety settings
    ("0x2620", "0x01", "Drive safety name"),
    ("0x2620", "0x02", "Safe fieldbus"),
    ("0x2620", "0x03", "Safe address"),
    # 0x2620:04 (FSoE Download) excluded — download trigger, not a stored parameter

    # Safety digital IO
    ("0x2621", "0x01", "Acknowledge via drive"),
    ("0x2621", "0x02", "Acknowledgement input"),
    ("0x2621", "0x03", "Input test pulse detection"),
    ("0x2621", "0x04", "Input filter time"),
    ("0x2621", "0x05", "Test pulse max. distance"),
    ("0x2621", "0x06", "Output test pulse"),
    ("0x2621", "0x07", "Output1 function"),
    ("0x2621", "0x08", "Output2 function"),

    # Safety IO analog input
    ("0x2625", "0x01", "Analog input1 Gain"),
    ("0x2625", "0x02", "Analog input1 Offset"),
    ("0x2625", "0x03", "Analog input2 Gain"),
    ("0x2625", "0x04", "Analog input2 Offset"),
    ("0x2625", "0x05", "Analog allowed error"),

    # Encoder source
    ("0x2630", "0x01", "Encoder source type"),
    ("0x2630", "0x02", "Encoder resolution"),
    ("0x2630", "0x03", "Encoder multiturn bits"),
    ("0x2630", "0x04", "Encoder clock frequency"),
    ("0x2630", "0x05", "Encoder timeout"),
    ("0x2630", "0x06", "Multiturn Counting by SMM"),

    # Encoder verification
    ("0x2631", "0x01", "Verification sensor source type"),
    ("0x2631", "0x02", "Verification sensor resolution"),
    ("0x2631", "0x03", "Verification sensor multiturn bits"),

    # Encoder selection
    ("0x2635", "0x01", "Speed window"),
    ("0x2635", "0x02", "Absolute position"),
    ("0x2635", "0x03", "Position reset input"),
    ("0x2635", "0x04", "Absolute position on reset"),
    ("0x2635", "0x05", "Allowed position discrepancy"),
    ("0x2635", "0x06", "Allowed speed discrepancy"),
    ("0x2635", "0x07", "Discrepancy timer"),
    ("0x2635", "0x08", "Verification scaling numerator"),
    ("0x2635", "0x09", "Verification scaling denominator"),

    # STO
    ("0x2641", "0x01", "STO input"),
    ("0x2641", "0x02", "SBC"),

    # SS1 input
    ("0x2650", "0x01", "SS1 input"),
    ("0x2650", "0x02", "SS1: Deceleration monitoring"),

    # SOS input
    ("0x2668", "0x01", "SOS input"),
    ("0x2668", "0x02", "t_D_SOS"),

    # SS2 input
    ("0x2670", "0x01", "SS2 input"),

    # SLS input
    ("0x2690", "0x01", "SLS1 input"),
    ("0x2690", "0x02", "SLS2 input"),
    ("0x2690", "0x03", "SLS3 input"),
    ("0x2690", "0x04", "SLS4 input"),

    # 0x26A0:00 (Reset position) excluded — operational command input, not a config value

    # Safe output
    ("0x26F0", "0x01", "Safe output 1"),
    ("0x26F0", "0x02", "Safe output 2"),

    # SS1 parameters
    ("0x6651", "0x01", "t_SS1"),
    ("0x6653", "0x01", "n_Zero_SS1"),
    ("0x6654", "0x01", "t_L_SS1"),
    ("0x6656", "0x01", "a_SS1"),
    ("0x6657", "0x01", "t_D_SS1"),

    # SBC
    ("0x6661", "0x00", "Brake time delay"),

    # SOS parameters
    ("0x666A", "0x01", "s_Zero_SOS"),
    ("0x666C", "0x01", "n_Zero_SOS"),

    # SS2 parameters
    ("0x6671", "0x01", "t_SS2"),
    ("0x6672", "0x01", "t_L_SS2"),
    ("0x6674", "0x01", "a_SS2"),
    ("0x6675", "0x01", "t_D_SS2"),
    ("0x6676", "0x01", "SOS restart"),
    ("0x6677", "0x01", "SS2 limit violation reaction"),

    # SLS parameters
    ("0x6691", "0x01", "t_SLS1"),
    ("0x6691", "0x02", "t_SLS2"),
    ("0x6691", "0x03", "t_SLS3"),
    ("0x6691", "0x04", "t_SLS4"),
    ("0x6692", "0x01", "n_SLS1"),
    ("0x6692", "0x02", "n_SLS2"),
    ("0x6692", "0x03", "n_SLS3"),
    ("0x6692", "0x04", "n_SLS4"),
    ("0x6694", "0x01", "t_L_SLS1"),
    ("0x6694", "0x02", "t_L_SLS2"),
    ("0x6694", "0x03", "t_L_SLS3"),
    ("0x6694", "0x04", "t_L_SLS4"),
    ("0x6695", "0x01", "t_D_SLS1"),
    ("0x6695", "0x02", "t_D_SLS2"),
    ("0x6695", "0x03", "t_D_SLS3"),
    ("0x6695", "0x04", "t_D_SLS4"),
    ("0x6696", "0x01", "a_SLS1"),
    ("0x6696", "0x02", "a_SLS2"),
    ("0x6696", "0x03", "a_SLS3"),
    ("0x6696", "0x04", "a_SLS4"),
    ("0x6698", "0x01", "SLS1 Limit violation reaction"),
    ("0x6698", "0x02", "SLS2 Limit violation reaction"),
    ("0x6698", "0x03", "SLS3 Limit violation reaction"),
    ("0x6698", "0x04", "SLS4 Limit violation reaction"),

    # SMS speed limits
    ("0x66AA", "0x00", "n_pos_max"),
    ("0x66AC", "0x00", "n_neg_max"),
    ("0x66AD", "0x00", "SMS Limit violation reaction"),
]

# Objects that carry a device-specific address — excluded when --skip-address.
ADDRESS_OBJECTS: set[tuple[str, str]] = {
    ("0x2620", "0x03"),  # Safe address
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read SMM safe-objects from a source device, build a config CSV, "
                    "and push it to one or more target devices."
    )
    parser.add_argument("--source", type=int, required=True, metavar="POS",
                        help="EtherCAT position of the source device (e.g. 3)")
    parser.add_argument("--targets", type=int, nargs="+", required=True, metavar="POS",
                        help="EtherCAT position(s) of the target device(s) (e.g. 27 28 29)")
    parser.add_argument("--url", default="http://localhost:63526/api",
                        help="Motion Master API base URL")
    parser.add_argument("--username", default="Test",
                        help="SMM username (default: Test)")
    parser.add_argument("--password", default="SomanetSMM",
                        help="SMM password (default: SomanetSMM)")
    parser.add_argument("--save", metavar="PATH",
                        help="Save the generated CSV to this path for inspection")
    parser.add_argument("--skip-address", action="store_true",
                        help="Exclude Safe address (0x2620:03) so each target keeps its own address")
    return parser.parse_args()


def read_smm_objects(device, skip_address: bool) -> list[tuple[str, str, str, object]]:
    """Read all SMM_OBJECTS from device. Returns list of (index, subindex, name, value)."""
    rows: list[tuple[str, str, str, object]] = []
    skipped = 0

    for index, subindex, name in SMM_OBJECTS:
        if skip_address and (index, subindex) in ADDRESS_OBJECTS:
            continue
        try:
            result = device.upload_parameter(index, subindex)
            value = result.get("value", result) if isinstance(result, dict) else result
            rows.append((index, subindex, name, value))
        except MotionMasterError as exc:
            print(f"  WARNING: skipping {index}:{subindex} ({name}) — {exc}", file=sys.stderr)
            skipped += 1

    print(f"  {len(rows)} objects read ({skipped} skipped due to errors).")
    return rows


def build_csv(rows: list[tuple[str, str, str, object]]) -> bytes:
    """Serialize rows to CSV bytes (index,subindex,value) without a header row."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    for index, subindex, _name, value in rows:
        writer.writerow([index, subindex, value])
    return buf.getvalue().encode()


def main() -> None:
    args = parse_args()

    system = System(args.url)
    system.connect()
    print(f"Connected to Motion Master at {args.url}")

    failed: list[int] = []
    try:
        # ------------------------------------------------------------------
        # Read SMM objects from source and build CSV
        # ------------------------------------------------------------------
        source = system.device(args.source)
        print(f"\nReading SMM objects from device at position {args.source} ...")
        if args.skip_address:
            print("  (FSoE address objects excluded — targets will keep their own addresses)")

        rows = read_smm_objects(source, skip_address=args.skip_address)
        config_bytes = build_csv(rows)
        print(f"  CSV size: {len(config_bytes)} bytes.")

        if args.save:
            with open(args.save, "wb") as fh:
                fh.write(config_bytes)
            print(f"  CSV saved to: {args.save}")

        # ------------------------------------------------------------------
        # Push config to each target
        # ------------------------------------------------------------------
        for pos in args.targets:
            print(f"\nCopying to device at position {pos} ...")
            target = system.device(pos)
            try:
                report = target.configure_smm(
                    config_bytes,
                    username=args.username,
                    password=args.password,
                )
                print("  OK — SMM configuration applied.")
                if report:
                    print(f"  Report:\n{report}")
            except MotionMasterError as exc:
                print(f"  FAILED (HTTP {exc.status_code}): {exc}", file=sys.stderr)
                failed.append(pos)
    finally:
        system.disconnect()
        print("\nDisconnected.")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    succeeded = [p for p in args.targets if p not in failed]
    print(f"Done. {len(succeeded)}/{len(args.targets)} device(s) updated successfully.")

    if failed:
        print(f"Failed positions: {failed}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
