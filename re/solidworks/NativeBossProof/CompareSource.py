from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
import json
from math import isclose, isfinite
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from GraphInventory import compare_documents, inspect_document, value_kind


def read(path, limit):
    with path.open("rb") as handle:
        payload = handle.read(limit + 1)
    if len(payload) > limit:
        raise ValueError("input exceeds its bounded evidence limit: " + path.name)
    return payload


def snapshot(directory):
    return {path.relative_to(directory).as_posix(): sha256(read(path, 64 * 1024 * 1024)).hexdigest() for path in sorted(directory.rglob("*")) if path.is_file()}


def graph(path, root):
    sys.path.insert(0, str(root / "src"))
    from interchange.document.Models.DocumentModel import CadDocument

    payload = read(path, 64 * 1024 * 1024)
    document = CadDocument.from_json(payload.decode("utf-8"))
    document.assert_valid()
    wire = document.to_dict()
    canonical = lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if canonical(json.loads(payload)) != canonical(wire):
        raise ValueError("typed reconstruction changed comparison document fields")
    return inspect_document(wire), document.source.sha256, sha256(payload).hexdigest()


def length_m(value):
    if type(value) is not dict or value_kind(value.get("kind")) != "length":
        return None
    number = value.get("value")
    if type(number) not in (int, float):
        return None
    try:
        if not isfinite(number):
            return None
    except OverflowError:
        return None
    scale = {"m": 1.0, "mm": 0.001}.get(value.get("unit"))
    return None if scale is None else number * scale


def depth_comparison(inventory, native):
    features = {entry["id"]: entry for entry in inventory["features"]}
    result = []
    for parameter in inventory["parameters"]:
        owner = features.get(parameter.get("owner_id"))
        if value_kind(parameter.get("role")) != "driving" or owner is None or owner["definition_type"] != "ExtrusionFeature":
            continue
        driver = length_m(parameter.get("value"))
        feature = length_m(owner["definition_length"])
        observed = native["depth_m"]
        result.append({
            "parameter_id": parameter["id"], "feature_id": owner["id"],
            "oracle_depth_m": observed, "driver_depth_m": driver, "feature_depth_m": feature,
            "driver_matches": driver is not None and isclose(driver, observed, rel_tol=1e-12, abs_tol=1e-12),
            "feature_matches": feature is not None and isclose(feature, observed, rel_tol=1e-12, abs_tol=1e-12),
            "retained_native_value": parameter.get("attributes", {}).get("native_value"),
            "retained_native_unit": parameter.get("attributes", {}).get("native_unit"),
        })
    return result


def recursive_comparison(inventory, native):
    rows = native.get("nested_features")
    if rows is None:
        return {"status": "not_observed", "occurrences": None}
    if type(rows) is not list:
        raise ValueError("recursive native feature observation must be a list")
    native_ids = {entry["id"] for entry in rows}
    sdk_ids = {entry["native_id"] for entry in inventory["features"] if type(entry["native_id"]) is int}
    mappings = []
    for entry in rows:
        candidates = [feature for feature in inventory["features"] if feature["native_id"] == entry["id"]]
        parent_ids = sorted({row["id"] for row in rows if row["name"] == entry.get("parent")}) if entry.get("parent") is not None else []
        parents = [feature for feature in inventory["features"] if feature["native_id"] in parent_ids]
        witness = None
        if entry.get("parent") is not None:
            witness = len(candidates) == len(parents) == 1 and (
                candidates[0]["id"] in parents[0]["input_feature_ids"]
                or parents[0]["id"] in candidates[0]["input_feature_ids"]
            )
        mappings.append({
            "native_id": entry["id"], "name": entry["name"], "native_type": entry["type"],
            "parent_name": entry.get("parent"), "parent_native_ids": parent_ids,
            "sdk_feature_ids": [feature["id"] for feature in candidates],
            "sdk_native_types": [feature["native_type"] for feature in candidates],
            "modeled_dependency_witness": witness,
            "type_equivalence": "not_proved_by_identifier_matching",
        })
    return {
        "status": "recorded_native_observation", "occurrences": len(rows), "unique_native_ids": len(native_ids),
        "native_only_ids": sorted(native_ids - sdk_ids), "sdk_only_ids": sorted(sdk_ids - native_ids),
        "rows": mappings,
    }


def captured(args):
    execution = None
    if args.run_directory is not None:
        if args.run_directory.exists():
            raise ValueError("run directory must be unused")
        command = args.root / "re/automation/EncoderRoundTrip/Command.py"
        execution = subprocess.run(
            [sys.executable, "-I", "-B", str(command), "--root", str(args.root), "run",
             "--application", "solidworks", "--source", str(args.source),
             "--output", str(args.run_directory), "--depth-mm", str(args.depth_mm),
             "--native-locator-directory", r"C:\KitA12bEvidence"],
            capture_output=True, text=True, timeout=180, check=False,
        )
        if execution.returncode not in (0, 3):
            raise ValueError("research command failed: " + execution.stdout + execution.stderr)
        directory = args.run_directory
    else:
        directory = args.capture
    if directory is None:
        return None, None, None
    manifest_bytes = read(directory / "manifest.json", 32 * 1024 * 1024)
    manifest = json.loads(manifest_bytes)
    if manifest["source"]["status"] != "decoded" or manifest.get("models_used") is not False:
        raise ValueError("capture is not a decoded deterministic source")
    document = directory / "document.json"
    document_sha = sha256(read(document, 64 * 1024 * 1024)).hexdigest()
    if manifest["neutral_sha256"] != document_sha or manifest["source"]["neutral"]["sha256"] != document_sha:
        raise ValueError("capture neutral bytes do not match the manifest")
    return document, directory, {
        "sdk_revision": manifest["sdk_revision"], "sdk_sources_sha256": manifest["sdk_sources_sha256"],
        "manifest_sha256": sha256(manifest_bytes).hexdigest(), "run_fingerprint": manifest["run_fingerprint"],
        "models_used": manifest["models_used"], "status": manifest["status"],
        "source_sha256": manifest["source_sha256"], "neutral_sha256": document_sha,
        "reconstruction": manifest["reconstruction"], "edited": manifest["edited"],
        "vendor_loadable": manifest["vendor_loadable"], "application_usable": manifest["application_usable"],
        "child_exit_code": None if execution is None else execution.returncode,
    }


def compare(args):
    args.root = args.root.resolve()
    args.source = args.source.resolve()
    native = read(args.source, 256 * 1024 * 1024)
    native_sha = sha256(native).hexdigest()
    definition_bytes = read(args.definition, 32 * 1024 * 1024)
    definition = json.loads(definition_bytes)
    authored = definition.get("authored", definition.get("samples"))
    if definition.get("passed") is not True or type(authored) is not dict:
        raise ValueError("definition must be the successful recorded native authoring result")
    key = args.definition_case or args.source.name
    expected = authored.get(key)
    if type(expected) is not dict or expected.get("sha256") != native_sha:
        raise ValueError("native source does not match its exact recorded authoring definition")
    document_path, directory, capture = captured(args)
    if args.document is not None:
        if document_path is not None:
            raise ValueError("select either captured or caller supplied neutral JSON")
        document_path = args.document
    if document_path is None:
        raise ValueError("a research capture or caller supplied neutral JSON is required")
    before = None if directory is None else snapshot(directory)
    inventory, document_source, document_sha = graph(document_path, args.root)
    if document_source != native_sha or (capture is not None and capture["source_sha256"] != native_sha):
        raise ValueError("neutral document does not bind the exact native source")
    oracle = expected.get("body", expected.get("api_observation"))
    if type(oracle) is not dict:
        raise ValueError("native definition lacks its independent API observation")
    tree = oracle["tree"]
    native_names = Counter(row["name"] for row in tree)
    sdk_names = Counter(row["name"] for row in inventory["features"])
    matches = []
    for row in tree:
        candidates = [feature for feature in inventory["features"] if feature["name"] == row["name"]]
        matches.append({"name": row["name"], "native_api_type": row["type"], "sdk_rows": candidates, "unique_name_match": len(candidates) == 1, "type_equivalence": "not_proved_by_name_matching"})
    blockers = []
    depths = depth_comparison(inventory, oracle)
    recursive = recursive_comparison(inventory, oracle)
    if len(depths) != 1 or any(not row["driver_matches"] or not row["feature_matches"] for row in depths):
        blockers.append("native_driving_depth_not_preserved")
    if inventory["native_property_status"] and inventory["native_property_status"].get("status") != "complete":
        blockers.append("native_property_scope_unqualified")
    if inventory["counts"]["brep_payloads"]:
        blockers.append("retained_native_payloads_require_typed_ownership")
    if inventory["unresolved_ownership_links"]:
        blockers.append("typed_body_or_graph_ownership_incomplete")
    if any(row["definition_type"] == "NativeFeatureDefinition" for row in inventory["features"]):
        blockers.append("native_feature_definitions_require_format_rules")
    if any(not row["closed_profile_entity_ids"] for row in inventory["sketches"]):
        blockers.append("closed_profile_binding_unavailable")
    if any(entity["geometry_type"] == "NativeGeometry" for row in inventory["sketches"] for entity in row["entities"]):
        blockers.append("opaque_sketch_geometry")
    if sdk_names != native_names:
        blockers.append("native_and_neutral_tree_views_require_explicit_presence_and_owner_mapping")
    comparison = None
    if args.compare_document is not None:
        other, other_source, other_sha = graph(args.compare_document, args.root)
        comparison = {"other_source_sha256": other_source, "other_document_sha256": other_sha, **compare_documents(inventory, other)}
    if directory is not None and before != snapshot(directory):
        raise ValueError("comparison mutated the settled research capture")
    if sha256(read(args.source, 256 * 1024 * 1024)).hexdigest() != native_sha:
        raise ValueError("native source changed during comparison")
    sdk_revision = subprocess.run(["git", "-C", str(args.root), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=30, check=True).stdout.strip()
    report = {
        "schema": "kit.sw2026.native-boss-comparison.v1", "sample_role": "unqualified_comparison",
        "source_name": args.source.name, "source_bytes": len(native), "source_sha256": native_sha,
        "definition_case": key, "definition_sha256": sha256(definition_bytes).hexdigest(),
        "native_authoring_identity": definition.get("oracle_identity"),
        "analysis_checkout_revision": sdk_revision, "capture": capture,
        "external_json_snapshot": capture is None, "neutral_sha256": document_sha,
        "native_api": {"top_level_tree_rows": len(tree), "tree": tree, "sketch_entities": len(oracle["sketch_segments"]), "sketch_relations": oracle["sketch_relations"], "depth_m": oracle["depth_m"], "bodies": oracle["bodies"], "volume_m3": oracle["volume_m3"], "centre_of_mass_m": oracle["centre_of_mass_m"], "document_properties": oracle.get("document_properties"), "expected_document_property": expected.get("expected_document_property")},
        "tree_name_comparison": {"native_only": list((native_names - sdk_names).elements()), "sdk_only": list((sdk_names - native_names).elements()), "rows": matches},
        "inventory": inventory, "driving_depth_comparison": depths, "recursive_native_comparison": recursive,
        "unresolved_requirements": blockers, "comparison": comparison,
        "native_processes_started": 0, "capture_unchanged": directory is not None,
        "native_acceptance": "not_established", "portable_complete": False,
        "admission_rule_confidence": "not found",
        "vendor_loadable": False, "application_usable": False,
        "method_sha256": {path.name: sha256(path.read_bytes()).hexdigest() for path in (Path(__file__), Path(__file__).with_name("GraphInventory.py"))},
    }
    if directory is not None and args.output.resolve().is_relative_to(directory.resolve()):
        raise ValueError("evidence output must not modify the settled research capture")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as target:
        json.dump(report, target, sort_keys=True, indent=2, allow_nan=False)
        target.write("\n")
    return {"source_sha256": native_sha, "neutral_sha256": document_sha, "sdk_feature_rows": inventory["counts"]["feature_timeline"], "native_api_top_rows": len(tree), "unresolved_requirements": blockers, "proof_sha256": sha256(args.output.read_bytes()).hexdigest(), "native_acceptance": "not_established"}


if __name__ == "__main__":
    parser = ArgumentParser(description="Compare exact native authoring definitions with typed neutral presence and ownership without qualifying conversion")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--definition", type=Path, required=True)
    parser.add_argument("--definition-case")
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--capture", type=Path)
    inputs.add_argument("--run-directory", type=Path)
    inputs.add_argument("--document", type=Path)
    parser.add_argument("--depth-mm", type=float, default=42.37)
    parser.add_argument("--compare-document", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    try:
        print(json.dumps(compare(parser.parse_args()), sort_keys=True, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(json.dumps({"error_type": type(error).__name__, "reason": str(error)}, sort_keys=True), file=sys.stderr)
        sys.exit(1)
