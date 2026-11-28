import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def execute(argv, *, request=None, root, env=None):
    with subprocess.Popen(argv, cwd=root, env=env, text=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
        try:
            stdout, stderr = process.communicate(None if request is None else json.dumps(request), timeout=90)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            raise ValueError(f"owned process timeout: {stderr[-1000:]}")
        return {"exit_code": process.returncode, "stdout": stdout, "stderr": stderr, "pid": process.pid}


def read_public(root, path, *, adapter_values=None):
    return execute([sys.executable, "-I", "-B", str(Path(__file__).with_name("PublicMateReadProcess.py")), "--root", str(root)], request={"path": str(path), "adapter_values": adapter_values}, root=root)


def signature(result):
    if result["exit_code"]:
        return {"exit_code": result["exit_code"], "error": result["stderr"].strip().splitlines()[-1]}
    value = json.loads(result["stdout"])
    return {"exit_code": 0, "document_json_sha256": digest(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())}


def compare(document, projection):
    assembly = document.assembly
    require(assembly is not None and len(assembly.mates) == 1 and len(assembly.mate_entities) == 2, "public mate inventory differs")
    mate = assembly.mates[0]
    expected = projection["mates"][0]
    require(mate.name == expected["name"] and str(mate.kind) == expected["kind"] and str(mate.alignment) == expected["alignment"], "mate semantic class name or alignment differs")
    if expected["driving_distance_m"] is None:
        require(mate.value is None, "non dimensional mate acquired a value")
    else:
        require(mate.value is not None and math.isclose(mate.value.value, expected["driving_distance_m"] * 1000, rel_tol=1e-12, abs_tol=1e-12) and mate.value.unit == "mm", "live distance or neutral units differ")
    require(mate.entity_ids == tuple(value.id for value in assembly.mate_entities), "mate entity order differs")
    for actual, target in zip(assembly.mate_entities, expected["entities"], strict=True):
        require(list(actual.instance_path) == target["instance_path"] and actual.source_entity_id == target["source_entity_id"], "actual occurrence or child datum differs")
        require(str(actual.kind) == "plane" and list(actual.attributes["stored_origin_m"]) == target["stored_origin_m"] and list(actual.attributes["stored_normal"]) == target["stored_normal"], "stored plane geometry differs")
        require(actual.attributes["native_child_update_stamp"] == target["child_update"] and actual.attributes["native_datum_name"] == target["datum_name"], "child stamp or datum name differs")
    report = document.metadata["solidworks.typed_mates_semantics"]
    require(report["status"] == "admitted" and report["full_selected_mate_graph"] and report["public_writer_qualified"] is False, "typed selected graph was not completely admitted")
    document.assert_valid()
    return {"mate_id": mate.id, "kind": str(mate.kind), "alignment": str(mate.alignment), "value_mm": None if mate.value is None else mate.value.value, "native_feature_id": mate.attributes["typed_archive_owner"]["native_feature_id"], "entity_ids": list(mate.entity_ids), "instance_paths": [list(value.instance_path) for value in assembly.mate_entities], "source_entity_ids": [value.source_entity_id for value in assembly.mate_entities], "map_base": report["map_base"], "map_terminal": report["map_terminal"], "valid": True, "projection_equal": True}


def code_manifest(root):
    rows = {}
    for folder in ("src", "re/tooling/sw2026", "tests/Convert/Solidworks/Research"):
        for path in sorted((root / folder).rglob("*.py")):
            rows[path.relative_to(root).as_posix()] = digest(path.read_bytes())
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--baseline-root", type=Path, required=True)
    parser.add_argument("--cohort", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root, baseline = args.root.resolve(), args.baseline_root.resolve()
    require(not args.output.exists(), "public process proof requires a new output directory")
    manifest_bytes = args.cohort.read_bytes()
    manifest = json.loads(manifest_bytes)
    rows = manifest["files"]
    require(len(rows) == 12 and len({row["sha256"] for row in rows}) == 12, "declared twelve input identities differ")
    for row in rows:
        data = Path(row["path"]).read_bytes()
        require(digest(data) == row["sha256"] and len(data) == row["bytes"], "declared input changed")
    code = code_manifest(root)
    before = code_manifest(baseline)
    args.output.mkdir(parents=True)
    source_bytes = (json.dumps({"current": code, "baseline": before}, indent=2, sort_keys=True) + "\n").encode()
    (args.output / "SourceManifest.json").write_bytes(source_bytes)
    sys.path.insert(0, str(root / "src"))
    from interchange import CadDocument

    reports, process_ids = [], []
    for index, parent in enumerate(row for row in rows if Path(row["path"]).suffix.upper() == ".SLDASM"):
        path = Path(parent["path"])
        children = [row for row in rows if Path(row["path"]).parent == path.parent and Path(row["path"]).suffix.upper() == ".SLDPRT"]
        require(len(children) == 1, "declared assembly does not have exactly one explicit child file")
        child = children[0]
        actual = read_public(root, path)
        process_ids.append(actual["pid"])
        require(actual["exit_code"] == 0, f"current public assembly read failed: {actual['stderr'][-1500:]}")
        (args.output / f"Assembly{index:02}.json").write_text(actual["stdout"])
        project = execute([sys.executable, "-B", str(root / "re/tooling/sw2026/serial/ProjectPlanarMates.py"), str(path), child["path"]], root=root, env={**os.environ, "PYTHONPATH": str(root / "src")})
        process_ids.append(project["pid"])
        require(project["exit_code"] == 0, f"independent graph projection failed: {project['stderr'][-1500:]}")
        (args.output / f"Projection{index:02}.json").write_text(project["stdout"])
        comparison = compare(CadDocument.from_json(actual["stdout"]), json.loads(project["stdout"]))
        previous = read_public(baseline, path)
        process_ids.append(previous["pid"])
        if index < 3:
            require(previous["exit_code"] == 0, "previous native assembly read regressed before comparison")
        else:
            require(previous["exit_code"] != 0 and "has no entities" in previous["stderr"], "previous generated failure differs")
        deferred = []
        for code_root in (baseline, root):
            result = read_public(code_root, path, adapter_values={"resolve_components": False})
            process_ids.append(result["pid"])
            deferred.append(signature(result))
        require(deferred[0] == deferred[1], "deferred component legacy behavior differs")
        part_reads = [read_public(code_root, Path(child["path"])) for code_root in (baseline, root)]
        process_ids.extend(result["pid"] for result in part_reads)
        require(signature(part_reads[0]) == signature(part_reads[1]) and part_reads[0]["exit_code"] == 0, "part public document JSON changed")
        reports.append({"file_sha256": parent["sha256"], "child_sha256": child["sha256"], "public_document_json_sha256": digest(actual["stdout"].encode()), "projection_json_sha256": digest(project["stdout"].encode()), "comparison": comparison, "previous_public": signature(previous), "deferred_behavior_equal": True, "deferred": deferred[0], "child_public_json_equal": True, "child_public": signature(part_reads[0])})
        print(json.dumps({"case": index + 1, "public": "passed", "projection_equal": True, "legacy_options_equal": True}), flush=True)
    require(code_manifest(root) == code and code_manifest(baseline) == before, "code closure changed during process proof")
    for row in rows:
        require(digest(Path(row["path"]).read_bytes()) == row["sha256"], "original input changed during proof")
    require(len(process_ids) == len(set(process_ids)) == 42, "public comparison process identities differ")
    receipt = {"schema": "solidworks-2026-public-typed-planar-mates-v1", "passed": True, "cohort_manifest_sha256": digest(manifest_bytes), "source_manifest_sha256": digest(source_bytes), "tool_sha256": digest(Path(__file__).read_bytes()), "process_count": len(process_ids), "process_ids": process_ids, "distinct_processes": True, "cases": reports, "prior_native_successes_preserved": 3, "prior_generated_empty_entity_failures_repaired": 3, "native_processes_started": 0, "heldout_inputs_read": False, "writer_output_count": 0, "native_acceptance_claim": False, "full_family_coverage": False, "original_inputs_unchanged": True}
    result_bytes = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode()
    (args.output / "PublicMateReadResults.json").write_bytes(result_bytes)
    print(json.dumps({"passed": True, "cases": len(reports), "process_count": len(process_ids), "receipt_sha256": digest(result_bytes)}))


if __name__ == "__main__":
    main()
