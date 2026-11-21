import argparse
from base64 import b64decode
import json
from pathlib import Path, PureWindowsPath
import shutil
import subprocess
import sys
from hashlib import sha256


def digest(data):
    return sha256(data).hexdigest()


def write(path, value):
    data = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    path.write_bytes(data)
    return digest(data)


def tree_rows(request):
    types = {"moCommentsFolder_c": "CommentsFolder", "moFavoriteFolder_c": "FavoriteFolder", "moHistoryFolder_c": "HistoryFolder", "moSelectionSetFolder_c": "SelectionSetFolder", "moSensorFolder_c": "SensorFolder", "moLiveSectionFolder_c": "LiveSectionFolder", "moDocsFolder_c": "DocsFolder", "moEnvFolder_c": "EnvFolder", "moInkMarkupFolder_c": "InkMarkupFolder", "moEqnFolder_c": "EqnFolder", "moMaterialFolder_c": "MaterialFolder", "moSolidBodyFolder_c": "SolidBodyFolder", "moSurfaceBodyFolder_c": "SurfaceBodyFolder"}

    def folders(values, cabinet):
        rows = []
        for kind, name in values:
            rows.append([name, types[kind], None])
            if kind == "moDocsFolder_c":
                rows.extend(([cabinet, "DetailCabinet", None], ["Notes", "NotesAreaFtrFolder", cabinet], ["Notes1___EndTag___", "NotesAreaFtrFolder", cabinet]))
            if kind == "moEnvFolder_c":
                rows.append(["Ambient", "AmbientLight", name])
                rows.extend([f"Directional{index}", "DirectionLight", name] for index in (1, 2, 3))
        return rows

    assembly = request["assembly"]["system"]
    parent = folders(assembly["folders"], assembly["cabinet_name"])
    parent.extend([assembly["planes"][axis], "RefPlane", None] for axis in ("z", "y", "x"))
    parent.append([assembly["origin_name"], "OriginProfileFeature", None])
    parent.extend([item["name"], "Reference", None] for item in request["occurrences"])
    parent.extend(([assembly["mate_group_name"], "MateGroup", None], [request["mate"]["name"], "MateDistanceDim", assembly["mate_group_name"]]))
    system = request["child"]["settings"]["system"]
    child = folders(system["folders"], system["cabinet_name"])
    child.extend([system["planes"][axis], "RefPlane", None] for axis in ("z", "y", "x"))
    child.extend(([system["origin_name"], "OriginProfileFeature", None], ["Sketch1", "ProfileFeature", None], ["Boss-Extrude1", "Extrusion", None]))
    return {"parent": parent, "child": child, "basis": "authored native roles and previously measured automatic cabinet and environment expansion", "observed_for_this_pair": False}


def prediction(request):
    from interchange.serialization.Deserialize import FromData
    document = FromData(request["child"]["document"])
    if document.units != "mm":
        raise ValueError("the disclosed native fixture prediction requires its authored millimetre plain rectangle")
    vertices = tuple((entity.geometry.start.x * 0.001, entity.geometry.start.y * 0.001) for entity in document.sketches[0].entities)
    width = max(point[0] for point in vertices) - min(point[0] for point in vertices)
    height = max(point[1] for point in vertices) - min(point[1] for point in vertices)
    depth = document.feature_timeline[0].definition.length.value * 0.001
    if min(point[0] for point in vertices) != -width / 2 or min(point[1] for point in vertices) != -height / 2:
        raise ValueError("the disclosed native fixture prediction requires its explicitly centered rectangle")
    volume, area = width * height * depth, 2 * (width * height + width * depth + height * depth)
    distance = request["mate"]["distance_m"]
    edited = distance + 0.01675
    first = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0]
    original = [*first[:9], distance, 0.1074, 0.0123, *first[12:]]
    changed = [*first[:9], edited, 0.1074, 0.0123, *first[12:]]
    return {"scope": "one sdk plain generated child two identity oriented resolved occurrences one aligned positive Right Plane distance and a fixed first occurrence",
            "child_dimensions_m": {"width": width, "height": height, "depth": depth}, "rectangle_position": "centered",
            "child_configuration": document.configurations[0].name, "assembly_configuration": request["assembly"]["configuration_name"], "sketch_dimensions_authored": False,
            "child_parameters_m": {"D1@Sketch1": None, "D2@Sketch1": None, "D1@Boss-Extrude1": depth},
            "initial": {"body_count": 2, "child": {"body_count": 1, "volume": volume, "area": area, "com": [0, 0, depth / 2]},
                        "assembly": {"volume": 2 * volume, "area": 2 * area, "com": [distance / 2, 0.1074 / 2, depth / 2 + 0.0123 / 2]},
                        "occurrence_transforms": [first, original], "fixed_flags": [True, False], "mate_distance_m": distance},
            "edited": {"body_count": 2, "child": {"body_count": 1, "volume": volume, "area": area, "com": [0, 0, depth / 2]},
                       "assembly": {"volume": 2 * volume, "area": 2 * area, "com": [edited / 2, 0.1074 / 2, depth / 2 + 0.0123 / 2]},
                       "occurrence_transforms": [first, changed], "fixed_flags": [True, False], "mate_distance_m": edited},
            "edit": {"parameter": "D1@Distance1", "full_name": "D1@Distance1@" + request["assembly"]["name"] + ".Assembly", "new_value_m": edited, "setter_status": 0},
            "ordered_endpoints": [{"occurrence": row["name"], "datum": "Right Plane", "datum_type": "RefPlane"} for row in request["occurrences"]],
            "tree": tree_rows(request), "save_order": ["child", "parent"], "fresh_reopen_required": True, "native_errors_expected": 0, "native_warnings_expected": 0,
            "controls": {"profile": "disclosed A18PlaneDistance with CohortChild.SLDPRT", "relative_directory": "AssemblyMateSource02/A18PlaneDistance/author", "fresh_healthy_before_and_after_required": True},
            "native_acceptance": False, "heldout_inputs_read": 0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--source-manifest-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--target-name")
    args = parser.parse_args()
    proof = args.proof.resolve(strict=True)
    source_data = (proof / "SourceManifest.json").read_bytes()
    if digest(source_data) != args.source_manifest_sha256:
        raise ValueError("writer source snapshot identity differs")
    manifest = json.loads(source_data)
    root = proof / "CodeRoot"
    for name, row in manifest["files"].items():
        if digest((root / name).read_bytes()) != row["sha256"]:
            raise ValueError("writer source changed before fixture generation")
    qualification = json.loads((proof / "SdkAssemblyResults.json").read_bytes())
    if not qualification["passed"] or qualification["source_manifest_sha256"] != args.source_manifest_sha256:
        raise ValueError("SDK complete assembly source process proof is not qualified")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    frozen = output / "FrozenGenerated"
    frozen.mkdir()
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(root), str(root / "src")]
    from tests.Convert.Solidworks.Research.Construction.Assembly.MakeAsmCase import MakeAsmCase
    request = MakeAsmCase("distance", "x", False)
    parent_name = request["assembly"]["name"] + ".SLDASM"
    child_name = PureWindowsPath(request["child"]["settings"]["output"]["path_name"]).name
    target = PureWindowsPath(r"\\Mac\Home\Documents\UniCAD\Oracle121Takeover") / (args.target_name or output.name) / "GeneratedInput"
    request["assembly"]["output"]["path_name"] = str(target / parent_name)
    request["child"]["settings"]["output"]["path_name"] = str(target / child_name)
    request["occurrences"][0]["origin"] = [0.0, 0.0, 0.0]
    request["occurrences"][1]["origin"] = [0.04353, 0.1074, 0.0123]
    request["mate"].update(name="Distance1", distance_m=0.04353)
    request_bytes = json.dumps(request, separators=(",", ":"), allow_nan=False).encode()
    (output / "NeutralRequest.json").write_bytes(request_bytes)
    prediction_sha = write(output / "Prediction.json", prediction(request))
    results = []
    for phase in ("BuildA", "BuildB", "Prepare", "Counterpart"):
        entry = "SdkAssemblyProcess.py" if phase.startswith("Build") else "SdkAssemblyVerify.py" if phase == "Prepare" else "SdkAssemblyCounterpart.py"
        incoming = request_bytes if phase.startswith("Build") else json.dumps({"request": request, "build": results[0]}, allow_nan=False).encode()
        result = subprocess.run([sys.executable, "-I", "-B", str(root / "re/tooling/sw2026" / entry), str(root)], input=incoming, capture_output=True, timeout=120)
        (output / (phase + ".stdout")).write_bytes(result.stdout)
        (output / (phase + ".stderr")).write_bytes(result.stderr)
        if result.returncode:
            raise ValueError(phase + " failed: " + result.stderr.decode()[-3000:])
        data = json.loads(result.stdout)
        if not data["passed"] or data["runtime_input_file_reads"]:
            raise ValueError("native fixture generation crossed its input boundary")
        results.append(data)
    for kind, name in (("assembly", parent_name), ("child", child_name)):
        if results[0][kind] != results[1][kind]:
            raise ValueError("two fresh SDK builds differ")
        (frozen / name).write_bytes(b64decode(results[0][kind]["blob"], validate=True))
    files = {path.name: {"bytes": path.stat().st_size, "sha256": digest(path.read_bytes()), "encoded_path": str(target / path.name)} for path in frozen.iterdir()}
    fixture = {"schema": "kit.sw2026.sdk-complete-assembly-native-fixture.v1", "source_manifest_sha256": args.source_manifest_sha256,
               "source_process_result_sha256": digest((proof / "SdkAssemblyResults.json").read_bytes()), "source_code_root": str(root),
               "preparer_sha256": digest(Path(__file__).read_bytes()), "request_sha256": digest(request_bytes), "prediction_sha256": prediction_sha,
               "files": files, "phase_receipts": {phase: digest((output / (phase + ".stdout")).read_bytes()) for phase in ("BuildA", "BuildB", "Prepare", "Counterpart")},
               "typed_stream_round_trips": results[2]["round_trips"], "independent_composer_matches": results[3]["same_as_independent_research"],
               "native_acceptance": False, "heldout_inputs_read": 0, "native_processes_started": 0}
    fixture_sha = write(output / "Fixture.json", fixture)
    shutil.copyfile(proof / "SourceManifest.json", output / "SourceManifest.json")
    print(json.dumps({"fixture": str(output / "Fixture.json"), "fixture_sha256": fixture_sha, "source_manifest_sha256": args.source_manifest_sha256, "prediction_sha256": prediction_sha, "files": files}, sort_keys=True))


if __name__ == "__main__":
    main()
