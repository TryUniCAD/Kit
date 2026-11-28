from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "serial"))
sys.path.insert(0, str(ROOT / "src"))

from Classes import registry
from builders.Part import construct_part
from convert.adapters.solidworks.Container.Container import build_sldprt


def main():
    parser = argparse.ArgumentParser(description="Construct an experimental 2026 part from neutral JSON")
    parser.add_argument("input", help="neutral JSON path, or - for standard input")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    request = json.load(sys.stdin) if args.input == "-" else json.loads(Path(args.input).read_text(encoding="utf-8"))
    part = construct_part(registry=registry(), **request)
    data = build_sldprt(part.streams)
    args.output.write_bytes(data)
    print(json.dumps({
        "output": str(args.output), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
        "streams": {name: len(value) for name, value in part.streams.items()},
        "vendor_acceptance": "unverified", "production_adapter": "read-only",
    }))


if __name__ == "__main__":
    main()
