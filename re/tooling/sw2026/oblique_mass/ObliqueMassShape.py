import argparse
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
import sys

CONTROL_RECORDS = {
    "ControlBefore": "e0cec59851b7404ce0337cdf0659c1c13ce722dc2df2d72d1475dd7a2392ef85",
    "ControlAfter": "da417cdd044a3b61a074fb767129e223e148a894a74d65e7c24b55d214d83c7b",
}


def require(value, message):
    if not value:
        raise ValueError(message)


def shape(value, depth=0):
    kind = type(value)
    result = {"type": kind.__module__ + "." + kind.__qualname__}
    if kind in (tuple, list):
        result["count"] = len(value)
        if depth < 3:
            result["items"] = [shape(item, depth + 1) for item in value[:16]]
            result["truncated"] = len(value) > 16
    elif kind in (int, float):
        result["finite"] = isfinite(value)
        result["value"] = value if result["finite"] else str(value)
    elif value is None or kind in (bool, str):
        result["value"] = value if kind is not str or len(value) <= 128 else value[:128]
    return result


def document_values(raw, level):
    require(
        type(level) is int and level in (0, 1, 2),
        "unexpected document accuracy argument",
    )
    require(
        type(raw) in (tuple, list) and len(raw) == 2,
        "document mass must return variant and actual status",
    )
    values, status = raw
    require(
        type(status) is int and status == 0, "actual document mass status is not OK"
    )
    require(
        type(values) in (tuple, list) and len(values) in (12, 13),
        "document mass variant has an unqualified metric shape",
    )
    require(
        all(type(item) in (int, float) and isfinite(item) for item in values),
        "document mass variant contains nonfinite or nonnumeric fields",
    )
    data = [float(item) for item in values]
    tail = []
    if len(data) == 13:
        require(
            type(values[12]) is float and values[12] == float(level),
            "observed 2026 trailing mass value differs from requested accuracy",
        )
        tail.append(
            {
                "index": 12,
                "value": data[12],
                "equals_requested_accuracy": True,
                "semantic_role": "observed extension value; internal meaning not generalized",
            }
        )
    return data[:12], {
        "status": status,
        "metric_layout": (
            "documented-twelve" if len(data) == 12 else "measured-2026-thirteen"
        ),
        "document_raw_values": data,
        "extension_tail": tail,
        "all_extension_semantics_proven": not tail,
    }


def replay(root):
    rows = []
    for phase, expected in CONTROL_RECORDS.items():
        path = root / phase / "Record.json"
        require(
            sha256(path.read_bytes()).hexdigest() == expected,
            "disclosed control record differs",
        )
        record = json.loads(path.read_bytes())
        source = record["result"]["mass_precision"]
        failures = source["levels"]
        require(
            len(failures) == 3
            and all(
                row["passed"] is False
                and row["status"] == 0
                and row["error"]
                == "ValueError('native mass result must contain twelve metrics')"
                for row in failures
            ),
            "preserve all original parser failures",
        )
        calls = [
            row
            for row in record["api_calls"]
            if row["method"].startswith("registered GetMassProperties2 accuracy ")
        ]
        require(len(calls) == 3, "disclosed control accuracy calls are incomplete")
        for level, call in enumerate(calls):
            require(call["method"].endswith(str(level)), "accuracy call order differs")
            values, framed = document_values(call["result"], level)
            default = source["original_default"]
            require(
                values[:3] == default["com"]
                and values[3] == default["volume"]
                and values[4] == default["area"],
                "document metric prefix differs from pristine analytic/default control",
            )
            rows.append(
                {
                    "phase": phase,
                    "accuracy": level,
                    "source_record_sha256": expected,
                    "recorded_json_shape": shape(call["result"]),
                    "framing": framed,
                    "original_failure_preserved": True,
                    "prefix_matches_pristine_control": True,
                }
            )
    return {
        "schema": "kit.sw2026.oblique-mass-shape-replay.v1",
        "passed": True,
        "replayed_calls": len(rows),
        "rows": rows,
        "native_processes_started": 0,
        "heldout_reads": 0,
        "native_acceptance": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("replay", "parse"))
    parser.add_argument("--controls", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.mode == "replay":
        result = replay(args.controls)
    else:
        request = json.load(sys.stdin)
        values, framing = document_values(request["raw"], request["accuracy"])
        result = {"values": values, "framing": framing}
    if args.output is not None:
        require(not args.output.exists(), "replay receipt must be unused")
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(
        json.dumps(
            (
                result
                if args.output is None
                else {
                    "passed": True,
                    "sha256": sha256(args.output.read_bytes()).hexdigest(),
                }
            ),
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
