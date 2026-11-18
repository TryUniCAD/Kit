from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def literal(values):
    result = {}
    for name, value in values.items():
        if value["type"] != 30 or value["raw"] != value["resolved"] or value["linked"]:
            raise ValueError("independent native observation is not ordinary literal text")
        result[name] = value["raw"]
    return result


def native_expected(record):
    result = json.loads(record.read_text())["result"]
    rebuilt = result.get("states", result)["rebuilt"]
    return {
        "summary": {key: value for key, value in rebuilt["summary"].items() if value},
        "document": literal(rebuilt["document"]),
        "configured": literal(rebuilt["configured"]),
        "configuration_name": rebuilt["configuration"],
        "expected_record_sha256": digest(record),
    }


def authored_expected(root, case):
    request = root / "SdkPartPropertiesNative02" / case / "Request.json"
    document = json.loads(request.read_text())["document"]
    configuration, = document["configurations"]["$tuple"]
    return {
        "summary": document["metadata"]["document_summary"],
        "document": document["metadata"]["custom_properties"],
        "configured": configuration["attributes"]["custom_properties"],
        "configuration_name": configuration["name"],
        "expected_request_sha256": digest(request),
    }


def cases(root):
    base = root / "SdkPartPropertiesNative02"
    specs = (
        ("PolygonGenerated", base / "PropertyPolygonDiscovery/PropertyPolygonDiscovery.SLDPRT", "0d3ec3a66fa50793bc54f18d2b9b16cf5aef7a58545f2cd527b2c1a240922062", authored_expected(root, "PropertyPolygonDiscovery")),
        ("CircleGenerated", base / "PropertyCircleDiscovery/PropertyCircleDiscovery.SLDPRT", "392c5b51b63761f4bba2baf6dc0715de4af8d3e5036b83a42e0f388031cc6edd", authored_expected(root, "PropertyCircleDiscovery")),
        ("PolygonSaved", base / "Inspection/polygonEdit/PropertyPolygonDiscoveryEdited.SLDPRT", "e311ba0626114291e62aacd26f705c8d304baa5d0315f89972fdde66bdee1f14", native_expected(base / "Inspection/polygonEdit/Record.json")),
        ("CircleSaved", base / "Inspection/circleEdit/PropertyCircleDiscoveryEdited.SLDPRT", "8007d21df3db5fc58c23d3fe589cfc15cf274ac83d9b2daa4878ee792e104e30", native_expected(base / "Inspection/circleEdit/Record.json")),
        ("CircleAuthored", root / "PartPropertySource01/Inspection/CircularPropertiesAuthor/CircularProperties.SLDPRT", "1c1bc718661b88a119bc3ac041f97d56cf5b4a06e290e1ac1afc79d423e42d23", native_expected(root / "PartPropertySource01/Inspection/CircularPropertiesAuthor/Record.json")),
    )
    for name, path, expected_sha, expected in specs:
        if digest(path) != expected_sha:
            raise ValueError("disclosed property source identity changed: " + name)
        yield name, path, expected_sha, expected


def check(document, expected):
    metadata = document["metadata"]
    if metadata["solidworks.part_text_properties"]["status"] != "complete":
        raise ValueError("normal reader did not admit the complete property projection")
    config, = document["configurations"]["$tuple"]
    actual = {
        "summary": metadata["document_summary"],
        "document": metadata["custom_properties"],
        "configured": config["attributes"]["custom_properties"],
        "configuration_name": config["name"],
    }
    if actual != {key: expected[key] for key in actual}:
        raise ValueError("normal public property dictionaries differ from their independent authored/native expectation")
    if config["attributes"]["native_configuration_id"] != 0:
        raise ValueError("normal reader lost the actual native configuration identity")
    return actual


def advanced_negative(root, source_root, outdir):
    path = source_root / "PartPropertySource01/Inspection/RectanglePropertiesAuthor/RectangleProperties.SLDPRT"
    expected_sha = "4377bf5680f30d1c9de52227928911e55604a75d30ceb987240df00d6b1b1805"
    if digest(path) != expected_sha:
        raise ValueError("advanced negative source identity changed")
    process = subprocess.run([sys.executable, "-B", str(root / "re/tooling/sw2026/ReadPartTextProbe.py"), str(root), str(path)],
                             capture_output=True, text=True, timeout=120, check=False)
    (outdir / "AdvancedNegative.stdout.json").write_text(process.stdout)
    (outdir / "AdvancedNegative.stderr.txt").write_text(process.stderr)
    if process.returncode:
        raise ValueError("advanced optional property failure regressed normal native reading: " + process.stderr)
    record = json.loads(process.stdout)
    document = record["document"]
    metadata = document["metadata"]
    if metadata["solidworks.part_text_properties"]["status"] != "unsupported":
        raise ValueError("advanced properties were incorrectly qualified")
    if {"document_summary", "custom_properties"} & metadata.keys() or any("custom_properties" in item["attributes"] for item in document["configurations"]["$tuple"]):
        raise ValueError("advanced property rejection leaked a partial projection")
    if not any(item["code"] == "solidworks.part_text_properties_unavailable" for item in document["diagnostics"]["$tuple"]):
        raise ValueError("advanced property rejection lost its information diagnostic")
    counts = {key: len(document[key]["$tuple"]) for key in ("feature_timeline", "sketches", "parameters")}
    if not all(counts.values()) or digest(path) != expected_sha or record["vendor_runtime_imports"]:
        raise ValueError("advanced negative lost existing geometry/history or crossed its boundary")
    return {"case": "AdvancedRectangleNegative", "file_sha256": expected_sha, "process_exit_code": process.returncode,
            "process_stdout_sha256": sha256(process.stdout.encode()).hexdigest(), "property_status": "unsupported",
            "qualified_text_fields": 0, "information_diagnostic": True, "retained_counts": counts,
            "typed_cmgr_exact_round_trip": record["cmgr_round_trip"], "input_unchanged": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("disclosed_root", type=Path)
    parser.add_argument("outdir", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    args.outdir.mkdir(parents=True, exist_ok=False)
    source_files = sorted((root / "src").rglob("*.py"))
    source_files += [Path(__file__).resolve(), root / "re/tooling/sw2026/ReadPartTextProbe.py"]
    source_manifest = {str(path.relative_to(root)): digest(path) for path in source_files}
    source_bytes = json.dumps(source_manifest, sort_keys=True, indent=2).encode() + b"\n"
    (args.outdir / "SourceManifest.json").write_bytes(source_bytes)
    rows = []
    for name, path, expected_sha, expected in cases(args.disclosed_root):
        command = [sys.executable, "-B", str(root / "re/tooling/sw2026/ReadPartTextProbe.py"), str(root), str(path)]
        process = subprocess.run(command, capture_output=True, text=True, timeout=120, check=False)
        (args.outdir / (name + ".stdout.json")).write_text(process.stdout)
        (args.outdir / (name + ".stderr.txt")).write_text(process.stderr)
        if process.returncode:
            raise ValueError("disclosed normal SDK property process failed: " + name + " " + process.stderr)
        record = json.loads(process.stdout)
        actual = check(record["document"], expected)
        if record["vendor_runtime_imports"] or record["native_processes_started"] or digest(path) != expected_sha:
            raise ValueError("normal read crossed its declared source/runtime boundary")
        rows.append({"case": name, "file_sha256": expected_sha, "expected_evidence": {key: value for key, value in expected.items() if key.startswith("expected_")},
                     "actual": actual, "cmgr_round_trip": record["cmgr_round_trip"], "cmgr_sha256": record["cmgr_sha256"],
                     "cmgr_map_counter": record["configuration_manager_map_counter"], "cmgr_property_records": record["cmgr_usage"]["schema_calls"].get("moCustomProperty", 0),
                     "process_exit_code": process.returncode, "process_stdout_sha256": sha256(process.stdout.encode()).hexdigest(), "input_unchanged": True})
    negative = advanced_negative(root, args.disclosed_root, args.outdir)
    if any(digest(root / path) != value for path, value in source_manifest.items()):
        raise ValueError("source closure changed during the disclosed property proof")
    result = {"schema": "kit.sw2026.part-text-reader-disclosed.v1", "passed": True,
              "source_manifest_sha256": sha256(source_bytes).hexdigest(), "source_file_count": len(source_manifest),
              "normal_public_processes": len(rows) + 1, "typed_cmgr_exact_round_trips": len(rows) + 1,
              "rows": rows, "advanced_negative": negative, "heldout_inputs_read": 0, "native_processes_started": 0,
              "native_acceptance": "previous disclosed lifecycle only; this proof is SDK reading"}
    (args.outdir / "Result.json").write_text(json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"passed": True, "processes": len(rows) + 1, "result_sha256": digest(args.outdir / "Result.json")}, sort_keys=True))


if __name__ == "__main__":
    main()
