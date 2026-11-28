from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

FAULTS = (
    "active-distance",
    "second-distance",
    "second-end",
    "chooser-owner",
    "consumes-output",
    "wrapper-atom",
)


def main():
    parser = argparse.ArgumentParser(
        description="Run the isolated disclosed through-all archive and end grammar through real process boundaries"
    )
    parser.add_argument("--sdk-root", type=Path, required=True)
    parser.add_argument("--case-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Use unused audit output")
    args.output.mkdir(parents=True)
    tools = Path(__file__).parent
    rows = {}
    for name, state, fault in [
        ("source", "source", None),
        ("edited", "edited", None),
        *((fault, "source", fault) for fault in FAULTS),
    ]:
        argv = [
            sys.executable,
            "-B",
            str(tools / "AuditThroughAllDisclosed.py"),
            "--sdk-root",
            str(args.sdk_root.resolve(strict=True)),
            "--case-root",
            str(args.case_root.resolve(strict=True)),
            "--state",
            state,
        ]
        if fault:
            argv.extend(("--fault", fault))
        result = subprocess.run(
            argv, capture_output=True, text=True, timeout=90, check=False
        )
        (args.output / (name + ".stdout.json")).write_text(
            result.stdout, encoding="utf-8"
        )
        (args.output / (name + ".stderr.txt")).write_text(
            result.stderr, encoding="utf-8"
        )
        if result.returncode or result.stderr:
            raise ValueError("The disclosed archive worker failed: " + name)
        parsed = json.loads(result.stdout)
        if (
            not parsed["passed"]
            or not parsed["file_unchanged"]
            or parsed["hidden_inputs_read"]
            or parsed["native_processes_started"]
            or parsed["writer_output_count"]
        ):
            raise ValueError("The disclosed archive worker crossed its boundary")
        rows[name] = parsed
    record = {
        "schema": "kit.sw2026.through-all-disclosed-read-process.v1",
        "source_case": "D01",
        "states": 2,
        "workers": len(rows),
        "round_trips": sum(
            len(row.get("typed_stream_round_trips", {})) for row in rows.values()
        ),
        "negative_cases": len(FAULTS),
        "results": rows,
        "python_version": sys.version,
        "passed": True,
        "tool_hashes": {
            path.name: sha256(path.read_bytes()).hexdigest()
            for path in sorted(tools.glob("*.py"))
        },
        "native_processes_started": 0,
        "hidden_inputs_read": 0,
        "writer_output_count": 0,
        "public_reader_enabled": False,
        "native_generated_acceptance": False,
    }
    output = args.output / "Result.json"
    output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "passed": True,
                "workers": len(rows),
                "round_trips": record["round_trips"],
                "negative_cases": len(FAULTS),
                "sha256": sha256(output.read_bytes()).hexdigest(),
                "hidden_inputs_read": 0,
                "native_processes_started": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
