import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path

from DecodedPairs import directory_pairs, file_pin, manifest_pairs
from SemanticComparison import (
    DOCUMENT_BYTES,
    QUANTITIES,
    compare_documents,
    document_input,
    tolerance_input,
)

MAX_BATCH_BYTES = 1024 * 1024 * 1024
ERRORS = (LookupError, OSError, TypeError, ValueError, OverflowError, RecursionError)
UNITS = ("mm", "cm", "m", "in", "ft")
PROGRAMME_PINS = {
    name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
    for name in ("CompareDecoded.py", "DecodedPairs.py")
}


def write_json(path, value, remaining):
    size = 0
    digest = hashlib.sha256()
    limit = min(DOCUMENT_BYTES, remaining)
    staged = path.with_name(path.name + ".partial")
    with staged.open("xb") as output:
        try:
            for chunk in json.JSONEncoder(
                sort_keys=True, separators=(",", ":"), allow_nan=False
            ).iterencode(value):
                content = chunk.encode("utf-8")
                size += len(content)
                if size > limit:
                    raise ValueError("comparison output exceeds its byte budget")
                output.write(content)
                digest.update(content)
            output.flush()
            os.fsync(output.fileno())
        except BaseException:
            output.close()
            staged.unlink()
            raise
    os.link(staged, path)
    staged.unlink()
    return {"path": path.name, "sha256": digest.hexdigest(), "size_bytes": size}


def compare_pair(pair, args, tolerances, tolerance_pin, pins):
    paths = {side: pair[side] for side in ("left", "right")}
    if any(path is None or not path.exists() for path in paths.values()):
        return {
            "status": "missing_input",
            "missing": [
                side for side, path in paths.items()
                if path is None or not path.exists()
            ],
        }
    for side, path in paths.items():
        pins[side] = file_pin(path, DOCUMENT_BYTES)
    documents = {
        side: document_input(path, pins[side]) for side, path in paths.items()
    }
    try:
        report = compare_documents(
            documents["left"], documents["right"], tolerances,
            args.left_unit, args.right_unit, args.max_candidates,
        )
    except ValueError as error:
        if str(error) not in {
            "semantic report exceeds its 33554432-byte JSON limit",
            "semantic graph issues exceed their output budget",
        }:
            raise
        report = {"status": "incomplete", "reason": str(error)}
    report["input_sha256"] = {**pins, "tolerances": tolerance_pin}
    for side, path in paths.items():
        file_pin_now = file_pin(path, DOCUMENT_BYTES)
        if file_pin_now != pins[side]:
            raise ValueError("comparison document changed during evaluation")
    return report


def result_counts(report):
    comparison = report.get("comparison", {})
    matches = comparison.get("matches", [])
    return {
        "matched_records": len(matches),
        "matched_features": sum(
            item["source_records"]["left"]["path"].startswith("/feature_timeline/")
            for item in matches
        ),
        "records_with_field_differences": sum(
            bool(item["differences"]) for item in matches
        ),
        **{
            key: len(comparison.get(key, []))
            for key in (
                "ambiguous", "unmatched_left", "unmatched_right",
                "reference_differences",
            )
        },
        "source_issues": sum(
            len(source["unresolved"])
            for source in report.get("sources", {}).values()
        ),
    }


def batch_exit(outcomes, rows):
    if outcomes["reader_error"] or outcomes["missing_input"]:
        return 1
    if any(outcomes[status] for status in ("ambiguous", "unresolved", "incomplete")):
        return 3
    if any(row["counts"]["source_issues"] for row in rows):
        return 3
    return 2 if outcomes["different"] else 0


def run_batch(args):
    if any(
        hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() != pin
        for name, pin in PROGRAMME_PINS.items()
    ):
        raise ValueError("bulk comparison implementation changed after import")
    if not 1 <= args.max_candidates <= 100000:
        raise ValueError("candidate budget must be between 1 and 100000")
    if args.manifest is not None:
        if args.left is not None or args.right is not None:
            raise ValueError("choose a manifest or two input directories")
        pairs, manifest_pin = manifest_pairs(args.manifest.absolute())
    else:
        if args.left is None or args.right is None:
            raise ValueError("supply both --left and --right or --manifest")
        pairs = directory_pairs(args.left.absolute(), args.right.absolute(), args.pattern)
        manifest_pin = None
    tolerances = dict.fromkeys(QUANTITIES, 0)
    tolerance_pin = hashlib.sha256(
        json.dumps(tolerances, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if args.tolerances is not None:
        tolerance_pin = file_pin(args.tolerances, 65536)
        tolerances = tolerance_input(args.tolerances, tolerance_pin)
    output = args.output.absolute()
    for root in (args.left, args.right):
        if root is not None and output.resolve().is_relative_to(root.resolve()):
            raise ValueError("output must be outside both input directories")
    if any(
        path is not None and path.resolve().is_relative_to(output.resolve())
        for pair in pairs for path in (pair["left"], pair["right"])
    ):
        raise ValueError("output must not contain an input document")
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    reports = output / "reports"
    reports.mkdir(mode=0o700)
    rows = []
    remaining = MAX_BATCH_BYTES - 2 * DOCUMENT_BYTES
    for index, pair in enumerate(pairs):
        pins = {"tolerances": tolerance_pin}
        try:
            report = compare_pair(pair, args, tolerances, tolerance_pin, pins)
        except ERRORS as error:
            report = {
                "status": "reader_error", "reason": str(error)[:4096],
                "error_type": type(error).__name__,
            }
        report["input_sha256"] = pins
        report["pair_id"] = pair["id"]
        report["semantic_qualification"] = "unverified"
        report["native_acceptance"] = "not_established"
        report_path = reports / f"{index:04d}.json"
        try:
            artifact = write_json(
                report_path, report, remaining - (len(pairs) - index) * 65536
            )
        except ValueError as error:
            report = {
                "pair_id": pair["id"], "status": "incomplete",
                "reason": str(error), "input_sha256": pins,
                "semantic_qualification": "unverified",
                "native_acceptance": "not_established",
            }
            artifact = write_json(report_path, report, remaining)
        remaining -= artifact["size_bytes"]
        artifact["path"] = "reports/" + artifact["path"]
        rows.append({
            "id": pair["id"], "status": report["status"],
            "inputs": {
                side: str(pair[side].absolute()) if pair[side] is not None else None
                for side in ("left", "right")
            },
            "input_sha256": report.get("input_sha256"),
            "counts": result_counts(report), "report": artifact,
        })
    outcomes = Counter(row["status"] for row in rows)
    exit_code = batch_exit(outcomes, rows)
    summary = {
        "batch_version": 1,
        "scope": "bulk_portable_semantic_graph_observation",
        "semantic_qualification": "unverified",
        "native_acceptance": "not_established",
        "pairing": "manifest" if args.manifest else "relative_path",
        "manifest_sha256": manifest_pin,
        "absolute_tolerances": tolerances,
        "tolerances_sha256": tolerance_pin,
        "geometry_units": {"left": args.left_unit, "right": args.right_unit},
        "max_candidates": args.max_candidates,
        "programme_sha256": PROGRAMME_PINS,
        "pair_count": len(rows), "outcomes": dict(outcomes),
        "exit_code": exit_code, "pairs": rows,
    }
    lines = [
        f"Compared {len(rows)} pairs; exit {exit_code}",
        "Semantic qualification: unverified; native acceptance: not established",
        *(
            f"{json.dumps(row['id'], ensure_ascii=True)}: {row['status']} "
            f"({row['counts']['matched_features']} feature correspondences) "
            f"{row['report']['path']}"
            for row in rows
        ),
    ]
    with (output / "summary.txt").open("x", encoding="utf-8") as target:
        target.write("\n".join(lines) + "\n")
    if any(
        hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() != pin
        for name, pin in PROGRAMME_PINS.items()
    ):
        raise ValueError("bulk comparison implementation changed during evaluation")
    write_json(output / "summary.json", summary, DOCUMENT_BYTES)
    print(json.dumps({
        "output": str(output), "pair_count": len(rows),
        "outcomes": dict(outcomes), "exit_code": exit_code,
    }, sort_keys=True))
    return exit_code


def main():
    parser = argparse.ArgumentParser(
        description="Compare decoded CadDocument JSON in bulk without running either decoder"
    )
    parser.add_argument("--left", type=Path, help="first export directory")
    parser.add_argument("--right", type=Path, help="second export directory")
    parser.add_argument("--manifest", type=Path, help="version 1 explicit JSON pair list")
    parser.add_argument("--pattern", default="*.json", help="relative path selection glob")
    parser.add_argument("--left-unit", choices=UNITS, required=True)
    parser.add_argument("--right-unit", choices=UNITS, required=True)
    parser.add_argument("--tolerances", type=Path, help="five absolute tolerances; default exact")
    parser.add_argument("--max-candidates", type=int, default=20000)
    parser.add_argument("--output", type=Path, required=True, help="unused output directory")
    try:
        args = parser.parse_args()
    except SystemExit as error:
        if error.code == 2:
            return 1
        raise
    try:
        return run_batch(args)
    except ERRORS as error:
        print(f"bulk comparison refused: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
