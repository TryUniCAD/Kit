from argparse import ArgumentParser
from hashlib import sha256
import json
import os
from pathlib import Path
from secrets import randbelow
import sys


RADIUS_INTERVALS_UM = (
    ((2100, 3400), (20100, 25900), (5001, 5431), (34700, 37900)),
    ((7850, 8850), (50105, 54105), (4549, 4921), (46820, 49100)),
)


def draw(interval, scale):
    low, high = interval
    return (low + randbelow(high - low + 1)) / scale


def main():
    parser = ArgumentParser()
    parser.add_argument("--method", type=Path, required=True)
    parser.add_argument("--method-pin", required=True)
    parser.add_argument("--disclosed-lock-pin", required=True)
    parser.add_argument("--intent-root", type=Path, required=True)
    parser.add_argument("--private-root", type=Path, required=True)
    args = parser.parse_args()

    if os.name != "nt" or not args.method.is_absolute() or args.method.drive.casefold() != "c:":
        raise ValueError("held-out source preparation requires the installed native guest")
    if sha256(args.method.read_bytes()).hexdigest() != args.method_pin:
        raise ValueError("disclosed method hash differs")

    tools = args.method.parent / "Tool"
    sys.path.insert(0, str(tools))
    from SealSweepSources import guest_private_path, prepare
    from SweepModel import PARAMETERS, SCHEMA, validate_spec

    source_root = guest_private_path(args.intent_root)
    capture_root = guest_private_path(args.private_root)
    if source_root.exists() or capture_root.exists() or source_root == capture_root:
        raise ValueError("held-out intention and test roots must be unused and distinct")
    cases = [
        {"name": f"Slot{slot:02d}",
         **{key: draw(interval, 1_000_000)
            for key, interval in zip(PARAMETERS, ranges, strict=True)}}
        for slot, ranges in enumerate(RADIUS_INTERVALS_UM, 1)
    ]
    spec = {"schema": SCHEMA, "cohort": "heldout",
            "density_kg_m3": draw((10811, 11721), 10), "cases": cases}
    validate_spec(spec)
    raw = (json.dumps(spec, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    source_root.mkdir(exist_ok=False)
    source = source_root / "Spec.json"
    with source.open("xb") as handle:
        handle.write(raw)
    frozen = prepare(args.method, args.method_pin, args.disclosed_lock_pin,
                     source, sha256(raw).hexdigest(), capture_root)
    print(json.dumps(frozen, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
