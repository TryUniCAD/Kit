import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PureWindowsPath
import subprocess
import sys


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return digest(path)


def require(value, message):
    if not value:
        raise ValueError(message)


def native_path(value):
    return Path.home().joinpath(*PureWindowsPath(value).relative_to(PureWindowsPath(r"\\Mac\Home")).parts)


def source_manifest(root):
    return {path.relative_to(root).as_posix(): digest(path) for path in sorted((root / "src").rglob("*.py"))}


def read_process(root, path):
    sys.path.insert(0, str(root / "src"))
    from convert import open_document

    document = open_document(path, include_brep=False, include_tessellation=False)
    document.assert_valid()
    forbidden = [name for name in sys.modules if name == "Swapp" or name == "pythoncom" or name.startswith("win32com")]
    require(not forbidden, "public native read imported a CAD runtime dependency")
    return {"document_json": document.to_json(indent=None), "com_imports": forbidden, "worker_pid": os.getpid(), "input_sha256": digest(path)}


def close_values(actual, expected):
    return len(actual) == len(expected) and all(math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-10) for a, b in zip(actual, expected, strict=True))


def compare(document, expected, prediction, child_sha):
    assembly = document.assembly
    require(assembly is not None and len(assembly.instances) == 2 and len(assembly.mates) == 3 and len(assembly.mate_entities) == 6,
            "the strict public reader lost the complete ordered assembly inventory")
    require([(row.name, row.active) for row in document.configurations] == [(prediction["assembly_configuration"], True)], "public parent configuration differs")
    require(len(assembly.documents) == 1, "the public pair must share one actual loaded child")
    child = assembly.documents[0].document
    require(child.source.sha256 == child_sha and [(row.name, row.active) for row in child.configurations] == [(prediction["child_configuration"], True)],
            "the public child file or active configuration differs")
    parameters = {row.name: row for row in child.parameters}
    require(set(parameters) == {"D1"} and parameters["D1"].value.unit == "mm"
            and math.isclose(parameters["D1"].value.value, prediction["child_dimensions_m"]["depth"] * 1000, rel_tol=1e-12),
            "the public child lost or added authored dimensions")
    by_name = {row.name: row for row in assembly.instances}
    names = prediction["ordered_endpoints"][0]["occurrences"]
    require(set(by_name) == set(names), "the public occurrence names differ")
    for index, name in enumerate(names):
        actual = by_name[name]
        matrix = expected["occurrence_transforms"][index]
        canonical = [matrix[0], matrix[3], matrix[6], matrix[9] * 1000, matrix[1], matrix[4], matrix[7], matrix[10] * 1000,
                     matrix[2], matrix[5], matrix[8], matrix[11] * 1000, 0.0, 0.0, 0.0, 1.0]
        require(actual.configuration_name == prediction["child_configuration"] and actual.fixed == expected["fixed_flags"][index]
                and close_values(actual.transform.values, canonical), "the public occurrence lost its selected configuration fixed flag or placement")
    entities = {row.id: row for row in assembly.mate_entities}
    planes = {row.name: row.id for row in child.support_planes}
    rows = []
    for actual, endpoint, relation in zip(assembly.mates, prediction["ordered_endpoints"], expected["constraints"], strict=True):
        require(actual.name == endpoint["mate"] and str(actual.kind) == endpoint["kind"] and str(actual.alignment) == "aligned" and not actual.suppressed,
                "the public ordered mate name kind or alignment differs")
        if relation["distance_m"] is None:
            require(actual.value is None, "a non dimensional public mate acquired a distance")
        else:
            require(actual.value is not None and actual.value.unit == "mm" and math.isclose(actual.value.value, relation["distance_m"] * 1000, rel_tol=1e-12),
                    "the public driving distance differs")
        require(len(actual.entity_ids) == 2, "a public planar mate lost an endpoint")
        for index, identity in enumerate(actual.entity_ids):
            entity = entities[identity]
            name, datum = endpoint["occurrences"][index], endpoint["datums"][index]
            axis = {"Right Plane": 0, "Top Plane": 1, "Front Plane": 2}[datum]
            matrix = expected["occurrence_transforms"][index]
            require(str(entity.kind) == "plane" and entity.instance_path == (by_name[name].id,) and entity.source_entity_id == planes[datum]
                    and entity.attributes["native_datum_name"] == datum and close_values(entity.attributes["stored_origin_m"], matrix[9:12])
                    and close_values(entity.attributes["stored_normal"], matrix[axis * 3:axis * 3 + 3]), "the public typed endpoint lost its actual occurrence or child principal plane")
        rows.append({"name": actual.name, "kind": str(actual.kind), "distance_mm": None if actual.value is None else actual.value.value,
                     "entity_ids": list(actual.entity_ids), "instance_paths": [list(entities[value].instance_path) for value in actual.entity_ids],
                     "source_entity_ids": [entities[value].source_entity_id for value in actual.entity_ids]})
    report = document.metadata["solidworks.typed_mates_semantics"]
    require(report["status"] == "admitted" and report["full_selected_mate_graph"], "the strict reader did not admit the complete selected mate graph")
    require(len({row.id for row in (*assembly.mates, *assembly.mate_entities)}) == 9, "public mate and entity identities collide")
    return {"valid": True, "mate_count": 3, "entity_count": 6, "actual_child_configuration": prediction["child_configuration"],
            "fixed_flags": [by_name[name].fixed for name in names], "child_d1_mm": parameters["D1"].value.value, "mates": rows,
            "full_selected_mate_graph": True, "independent_geometry_and_reference_prediction_matches": True}


def check(args):
    root = args.root.resolve(strict=True)
    trial = args.native_result.resolve(strict=True)
    require(digest(trial) == args.native_result_sha256, "the qualified native lifecycle result differs")
    result = json.loads(trial.read_bytes())
    require(result["passed"] and result["controls_healthy"] and result["distinct_processes"] == 4, "the native lifecycle is not qualified")
    base = args.base_packet.resolve(strict=True)
    require(digest(base) == result["base_packet_sha256"], "the original frozen SDK packet differs")
    job = json.loads(base.read_bytes())
    fixture = json.loads((base.parent / "Fixture.json").read_bytes())
    require(digest(base.parent / "Fixture.json") == job["fixture_sha256"], "the original fixture differs")
    prediction = json.loads((base.parent / "Prediction.json").read_bytes())
    require(digest(base.parent / "Prediction.json") == fixture["prediction_sha256"], "the independent prediction differs")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    source = source_manifest(root)
    source_sha = write(output / "SourceManifest.json", {"files": source, "tool_sha256": digest(Path(__file__))})
    pairs = {"assembly" if name.upper().endswith(".SLDASM") else "child": (name, row) for name, row in fixture["files"].items()}
    saved = result["phases"]["Generated"]["saved"]
    sys.path.insert(0, str(root / "src"))
    from interchange import CadDocument

    rows = []
    for role, state in (("Frozen", "initial"), ("Saved", "edited")):
        parent_name, parent = pairs["assembly"]
        child_name, child = pairs["child"]
        parent_path = base.parent / "FrozenGenerated" / parent_name if role == "Frozen" else native_path(parent["encoded_path"])
        child_path = base.parent / "FrozenGenerated" / child_name if role == "Frozen" else native_path(child["encoded_path"])
        parent_sha = parent["sha256"] if role == "Frozen" else saved["parent"]
        child_sha = child["sha256"] if role == "Frozen" else saved["child"]["native_sha256"]
        require(digest(parent_path) == parent_sha and digest(child_path) == child_sha, "the declared public input pair differs")
        process = subprocess.run([sys.executable, "-I", "-B", str(Path(__file__).resolve()), "read", "--root", str(root), "--file", str(parent_path)], capture_output=True, timeout=90)
        (output / (role + ".stdout")).write_bytes(process.stdout)
        (output / (role + ".stderr")).write_bytes(process.stderr)
        require(process.returncode == 0, "strict public read failed: " + process.stderr.decode()[-1200:])
        record = json.loads(process.stdout)
        require(record["input_sha256"] == parent_sha and not record["com_imports"], "the public worker read a different input or imported COM")
        document = CadDocument.from_json(record["document_json"])
        comparison = compare(document, prediction[state], prediction, child_sha)
        require(digest(parent_path) == parent_sha and digest(child_path) == child_sha, "the SDK read changed native inputs")
        rows.append({"role": role, "parent_sha256": parent_sha, "child_sha256": child_sha, "worker_pid": record["worker_pid"], "stdout_sha256": hashlib.sha256(process.stdout).hexdigest(),
                     "exit_code": process.returncode, "com_imports": record["com_imports"], "comparison": comparison})
    require(source_manifest(root) == source and len({row["worker_pid"] for row in rows}) == 2, "the public reader source or process identities differ")
    receipt = {"schema": "kit.sw2026.sdk-ordered-native-public-readback.v1", "native_result_sha256": args.native_result_sha256,
               "source_manifest_sha256": source_sha, "tool_sha256": digest(Path(__file__)), "cases": rows, "native_processes_started": 0,
               "heldout_inputs_read": 0, "writer_output_count": 0, "passed": True}
    receipt_sha = write(output / "Result.json", receipt)
    return {"passed": True, "result_sha256": receipt_sha, "cases": len(rows), "native_processes_started": 0}


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("read", "check"):
        child = commands.add_parser(name)
        child.add_argument("--root", type=Path, required=True)
    commands.choices["read"].add_argument("--file", type=Path, required=True)
    command = commands.choices["check"]
    command.add_argument("--native-result", type=Path, required=True)
    command.add_argument("--native-result-sha256", required=True)
    command.add_argument("--base-packet", type=Path, required=True)
    command.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = read_process(args.root.resolve(strict=True), args.file.resolve(strict=True)) if args.command == "read" else check(args)
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
