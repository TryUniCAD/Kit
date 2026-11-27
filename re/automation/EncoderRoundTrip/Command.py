import argparse
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "re" / "automation"), str(ROOT / "re"), str(ROOT / "src")]

from EncoderRoundTrip.Pipeline import APPLICATIONS, ROLES, run_round_trip
from EncoderRoundTrip.Receipts import attach_receipt


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Research-only deterministic native candidate generation and receipt attachment",
        allow_abbrev=False,
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", allow_abbrev=False)
    run.add_argument("--application", choices=APPLICATIONS, required=True)
    run.add_argument("--source", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--depth-mm", type=float, required=True)
    run.add_argument("--native-locator-directory")
    attach = commands.add_parser("attach-receipt", allow_abbrev=False)
    attach.add_argument("--output", type=Path, required=True)
    attach.add_argument("--role", choices=ROLES, required=True)
    attach.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.root.resolve() != ROOT:
            raise ValueError("root must be this round-trip tool's SDK checkout")
        if args.command == "attach-receipt":
            result = attach_receipt(args.output, args.role, args.receipt)
        else:
            result = run_round_trip(
                ROOT,
                args.source,
                args.output,
                args.application,
                {"dimension": "depth", "value_mm": args.depth_mm},
                native_locator_directory=args.native_locator_directory,
            )
        print(json.dumps(result, sort_keys=True, allow_nan=False))
        return 3 if result["status"] == "incomplete" else 0
    except (OSError, ValueError, RecursionError, subprocess.SubprocessError) as error:
        print(json.dumps({"error": str(error)[:2048], "error_type": type(error).__name__}, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
