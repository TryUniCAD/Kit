from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return sha256(canonical(value)).hexdigest()


def summarize(args):
    if re.fullmatch(r"[0-9a-f]{40}", args.inventory_commit) is None:
        raise ValueError("inventory origin must be an exact Git commit")
    repository = args.repository.resolve()
    files = sorted(args.input_directory.glob("*.json"))
    if not 1 <= len(files) <= 1000:
        raise ValueError("select a bounded nonempty full-inventory directory")
    cases = {}
    methods = None
    sdk_identity = None
    definitions = {}
    for path in files:
        if re.fullmatch(r"[A-Za-z]+\.json", path.name) is None:
            raise ValueError("unexpected full-inventory filename")
        raw = path.read_bytes()
        if len(raw) > 32 * 1024 * 1024:
            raise ValueError("full inventory exceeds 32 MiB")
        report = json.loads(raw)
        original_path = "re/solidworks/NativeBossProof/Evidence/" + path.name
        identity = args.inventory_commit + ":" + original_path
        original = subprocess.run(
            ["git", "-C", str(repository), "show", identity],
            capture_output=True, timeout=30, check=True,
        ).stdout
        if canonical(json.loads(original)) != canonical(report):
            raise ValueError("saved full inventory differs from its immutable Git record")
        blob = subprocess.run(
            ["git", "-C", str(repository), "rev-parse", identity],
            capture_output=True, text=True, timeout=30, check=True,
        ).stdout.strip()
        if report.get("schema") != "kit.sw2026.native-boss-comparison.v1":
            raise ValueError("unsupported full-inventory schema")
        if report["vendor_loadable"] is not False or report["application_usable"] is not False:
            raise ValueError("summary must not change this unqualified evidence scope")
        capture = report["capture"]
        current_sdk = {name: capture[name] for name in ("sdk_revision", "sdk_sources_sha256")}
        if methods is None:
            methods = report["method_sha256"]
            sdk_identity = current_sdk
        if report["method_sha256"] != methods or current_sdk != sdk_identity:
            raise ValueError("full inventories do not share their recorded method and SDK")
        definitions[report["definition_sha256"]] = report["native_authoring_identity"]
        inventory = report["inventory"]
        recursive = report["recursive_native_comparison"]
        comparison = report["comparison"]
        changed = [] if comparison is None else comparison["changed_records"]
        cases[path.stem] = {
            "source": {"name": report["source_name"], "bytes": report["source_bytes"], "sha256": report["source_sha256"]},
            "definition": {"case": report["definition_case"], "sha256": report["definition_sha256"]},
            "neutral_sha256": report["neutral_sha256"],
            "full_inventory": {"bytes": len(raw), "file_sha256": sha256(raw).hexdigest(), "git_blob": blob, "git_file_sha256": sha256(original).hexdigest()},
            "typed_inventory_sha256": digest(inventory),
            "typed_document_sha256": inventory["document_sha256"],
            "retained_spans": {"count": len(inventory["retained_byte_spans"]), "bytes": sum(row["bytes"] for row in inventory["retained_byte_spans"]), "sha256": digest(inventory["retained_byte_spans"])},
            "capture": {name: capture[name] for name in ("manifest_sha256", "run_fingerprint", "models_used", "status", "child_exit_code", "reconstruction", "edited")},
            "capture_unchanged": report["capture_unchanged"],
            "collection_counts": inventory["counts"],
            "native_api_top_rows": report["native_api"]["top_level_tree_rows"],
            "recursive_api": {name: value for name, value in recursive.items() if name != "rows"},
            "sdk_only_top_view_names": report["tree_name_comparison"]["sdk_only"],
            "driving_depth_comparison": report["driving_depth_comparison"],
            "public_body_topology": [body["topology"] for body in inventory["body_summaries"]],
            "brep_counts": inventory["brep_counts"],
            "unresolved_ownership": dict(sorted(Counter(row["relation"] for row in inventory["unresolved_ownership_links"]).items())),
            "opaque_sketch_entities": [{"id": entity["id"], "kind": entity["kind"], "geometry_type": entity["geometry_type"]} for sketch in inventory["sketches"] for entity in sketch["entities"] if entity["geometry_type"] == "NativeGeometry"],
            "native_property_status": inventory["native_property_status"],
            "expected_native_property": report["native_api"]["expected_document_property"],
            "unresolved_requirements": report["unresolved_requirements"],
            "comparison": None if comparison is None else {
                "sha256": digest(comparison), "other_document_sha256": comparison["other_document_sha256"],
                "other_source_sha256": comparison["other_source_sha256"], "policy": comparison["policy"],
                "equal": comparison["equal"], "changed_records": len(changed),
                "changed_collections": dict(sorted(Counter(row["collection"] for row in changed).items())),
                "ownership_changed": comparison["ownership_changed"], "root_fields_changed": comparison["root_fields_changed"],
            },
        }
    ledger = {
        "schema": "kit.sw2026.native-boss-inventory-ledger.v1",
        "sample_role": "discovery_only", "case_count": len(cases),
        "inventory_origin_commit": args.inventory_commit,
        "full_inventory_storage": "ignored task-owned output plus immutable origin Git blobs",
        "sdk_identity": sdk_identity, "comparison_method_sha256": methods,
        "summary_method_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "native_definition_records": definitions, "cases": cases,
        "native_acceptance": "not_established", "portable_complete": False,
        "vendor_loadable": False, "application_usable": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(ledger, output, sort_keys=True, indent=2, allow_nan=False)
        output.write("\n")
    print(json.dumps({"cases": len(cases), "ledger_sha256": sha256(args.output.read_bytes()).hexdigest(), "full_inventory_bytes": sum(row["full_inventory"]["bytes"] for row in cases.values())}, sort_keys=True))


if __name__ == "__main__":
    parser = ArgumentParser(description="Condense unchanged native boss inventories while preserving their complete content identities and process evidence")
    parser.add_argument("--input-directory", type=Path, required=True)
    parser.add_argument("--inventory-commit", required=True)
    parser.add_argument("--repository", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--output", type=Path, required=True)
    summarize(parser.parse_args())
