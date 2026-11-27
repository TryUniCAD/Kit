from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def digest(raw):
    return sha256(raw).hexdigest()


def summarize(directory):
    cases = {}
    common = None
    for name in ("Diagnostic", "LegacyNoise", "SameSessionNoise", "ToggleFirst"):
        folder = directory / name
        raw = (folder / "Comparison.json").read_bytes()
        report = json.loads(raw)
        if (
            report["schema"] != "kit.sw2026.plane-display-comparison.v1"
            or report["confidence"] != "not_found"
            or report["field_hypothesis"] is not None
        ):
            raise ValueError("unsupported or qualified comparison report")
        identity = {key: report[key] for key in ("sdk", "python", "method_sha256")}
        if common is None:
            common = identity
        if identity != common:
            raise ValueError("comparison methods or SDK sources differ")
        inventories = {}
        for role in ("before_inventory", "after_inventory", "typed_comparison"):
            artifact = report["artifacts"][role]
            data = (folder / artifact["path"]).read_bytes()
            if (
                digest(data) != artifact["sha256"]
                or len(data) != artifact["size_bytes"]
            ):
                raise ValueError("complete comparison artifact differs")
            inventories[role] = json.loads(data)
        source_roles = {}
        for role in ("before", "after"):
            source = report[role]
            tree = inventories[role + "_inventory"]
            definition = tree.get("definition_schema_only", {}).get("leaves", {})
            source_roles[role] = {
                "sha256": source["sha256"],
                "bytes": source["bytes"],
                "typed": source["typed"],
                "clear_streams": len(source["streams"]),
                "stream_inventory_sha256": digest(canonical(source["streams"])),
                "display_words_observed": [
                    definition.get("root/fad8_0"),
                    definition.get("root/fad8_1"),
                ],
                "typed_inventory_sha256": digest(canonical(tree)),
                "typed_counts": {
                    key: {
                        "owners": len(value["owners"]),
                        "leaves": len(value["leaves"]),
                        "next_index": value["map"]["next_index"],
                    }
                    for key, value in tree.items()
                },
            }
        cases[name] = {
            "report_sha256": digest(raw),
            "purpose": report["purpose"],
            **source_roles,
            "capture_receipt": report["receipt"],
            "changed_streams": [row["name"] for row in report["changed_streams"]],
            "typed_changes": report["typed_changes"],
            "full_artifacts": report["artifacts"],
        }
    first = (directory / "ToggleFirst/Comparison.json").read_bytes()
    repeated = (directory / "ToggleRepeated/Comparison.json").read_bytes()
    if first != repeated:
        raise ValueError("fresh repeated toggle report differs")
    for name, expected in common["method_sha256"].items():
        if digest(Path(__file__).with_name(name).read_bytes()) != expected:
            raise ValueError("comparison source differs from the measured method")
    checks_raw = (directory / "ProcessChecks.json").read_bytes()
    checks = json.loads(checks_raw)
    if not all(row["returncode"] == 1 and row["no_output_directory"] for row in checks):
        raise ValueError("process refusal evidence is incomplete")
    return {
        "schema": "kit.sw2026.plane-display-comparison-proof.v1",
        **common,
        "cases": cases,
        "fresh_comparison_processes": 5,
        "toggle_repeat_exact": True,
        "toggle_repeated_report_sha256": digest(repeated),
        "process_refusals": checks,
        "process_refusals_sha256": digest(checks_raw),
        "summary_method_sha256": digest(Path(__file__).read_bytes()),
        "confidence": "not_found",
        "field_rule_established": False,
        "vendor_loadable": False,
        "application_usable": False,
        "limits": [
            "discovery only; no reserved holdout read",
            "toggle capture crosses authoring lifetimes",
            "strict Definition admission remains refused",
            "schema-only parsing does not establish portable semantics",
            "full inventories remain in ignored output with exact hashes",
        ],
    }


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Summarize hash-bound offline plane-display comparisons without dropping their full evidence"
    )
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = summarize(args.directory)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as target:
        json.dump(report, target, sort_keys=True, indent=2)
        target.write("\n")
    print(
        json.dumps(
            {"cases": len(report["cases"]), "sha256": digest(args.output.read_bytes())},
            sort_keys=True,
        )
    )
