from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path, PureWindowsPath


WRITER = "23e01579fb0ad607417ddfc84e4fbb7b0c55b1be"
WRITER_TREE = "1d6a9ee722f57e061725b43671498bf6fa3968e2"
SOURCE_LOCK = "50de39dc21405cd346566f64244b62d457857758f339a95be4baf3466dfc1f80"
CHILD_MANIFEST = "7c84fd4ef75ecf5f8b0cf00fbc12e932aa7e7955ecb5bb414c22d309f9362e79"
CHILD_SPEC = "ad41ba0f173d296bfa863aa2ccf9373923a3e57532fd4b67f960960c3998075b"
CONTROL = "c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57"
EDITS = (("Width", "D1@Sketch1", 0.05), ("Height", "D2@Sketch1", 0.025), ("Depth", "D1@Boss-Extrude1", 0.0125))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checked_json(path, expected):
    data = path.read_bytes()
    if digest(data) != expected:
        raise ValueError(f"frozen authored input differs: {path.name}")
    return json.loads(data)


def json_bytes(value):
    return (json.dumps(value, indent=2, allow_nan=False) + "\n").encode()


def write(path, data):
    with path.open("xb") as output:
        output.write(data)
    return digest(data)


def export_source(repo, launch, root):
    paths = (
        "src", "re/tooling/sw2026/AssemblyRootProcess.py",
        "re/tooling/sw2026/builders", "re/tooling/sw2026/serial", "tests/__init__.py",
        "tests/Convert/__init__.py", "tests/Convert/Solidworks/__init__.py", "tests/Convert/Solidworks/Research",
    )
    rows = []
    for entry in launch("ls-tree", "-rz", WRITER, "--", *paths).split(b"\0"):
        if not entry:
            continue
        header, filename = entry.split(b"\t", 1)
        mode, kind, object_id = header.split(b" ")
        if mode not in (b"100644", b"100755") or kind != b"blob":
            raise ValueError("unexpected non-file entry in the frozen writer source")
        rows.append((object_id, filename.decode()))
    batch = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "--batch"],
        input=b"".join(object_id + b"\n" for object_id, _ in rows),
        capture_output=True, check=True,
    )
    with io.BytesIO(batch.stdout) as records:
        for object_id, filename in rows:
            found, kind, size = records.readline().strip().split()
            if (found, kind) != (object_id, b"blob"):
                raise ValueError("frozen source object identity differs")
            target = root / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            write(target, records.read(int(size)))
            if records.read(1) != b"\n":
                raise ValueError("invalid frozen Git stream framing")
    return len(rows)


def authoring_child(launcher):
    manifest = launcher("show", WRITER + ":re/solidworks/v2026/corpus/ladder/Manifest.json")
    if digest(manifest) != CHILD_MANIFEST:
        raise ValueError("independently authored L1 manifest differs")
    case, = [row["spec"] for row in json.loads(manifest)["records"] if row["source_sha256"] == CONTROL]
    if digest(json.dumps(case, sort_keys=True, separators=(",", ":")).encode()) != CHILD_SPEC:
        raise ValueError("independently authored L1 model intent differs")
    sketch, boss = case["ops"]
    width, height = sketch["dims"]
    annotations = {
        name: [value / 1000 for value in source["at"]]
        for name, source in (("width_text_m", width), ("height_text_m", height))
    }
    vertices = [[value / 1000 for value in line["p"][:2]] for line in sketch["entities"]]
    parameters = {"D1@Sketch1": width["value"] / 1000, "D2@Sketch1": height["value"] / 1000, "D1@Boss-Extrude1": boss["depth"] / 1000}
    neutral = {
        "name": "CohortChild", "configuration_name": "Default", "sketch_name": sketch["name"],
        "extrusion_name": "Boss-Extrude1", "vertices_m": vertices, "depth_m": boss["depth"] / 1000,
        "rectangle_dimensions": annotations | {"route_centerline": False},
    }
    return neutral, parameters


def occurrence(spec):
    axis = "xyz".index(spec["axis"])
    first, second = (axis + 1) % 3, (axis + 2) % 3
    translation = spec["translation_m"]
    theta = math.radians(spec["angle_deg"])
    if len(translation) != 3 or not all(math.isfinite(value) for value in [theta, *translation]):
        raise ValueError("placement requires a finite rotation and translation")
    basis = [0.0] * 9
    basis[axis * 3 + axis] = 1.0
    basis[first * 3 + first] = basis[second * 3 + second] = math.cos(theta)
    basis[first * 3 + second] = math.sin(theta)
    basis[second * 3 + first] = -math.sin(theta)
    return {"origin": translation, "u": basis[:3], "v": basis[3:6]}, [*basis, *translation, 1.0, 0.0, 0.0, 0.0]


def geometry(dimensions, *, edited=None):
    width, height, depth = (dimensions[name] for _, name, _ in EDITS)
    volume = width * height * depth
    center = [None, None, depth / 2] if edited in ("Width", "Height") else [0.0, 0.0, depth / 2]
    return {"volume": volume, "area": 2 * (width * height + width * depth + height * depth), "mass": volume, "center": center}


def compose_case(root, case, child, output_path):
    from tests.Convert.Solidworks.Research.Assembly.OccurrenceInput import MakeOccInput
    from tests.Convert.Solidworks.Research.Presentation.MakeTreeInput import MakeTreeInput

    name = case["name"]
    request = MakeOccInput(name, [0, 0, 0], [1, 0, 0], [0, 1, 0])
    request["assembly"]["output"]["path_name"] = str(output_path / (name + ".SLDASM"))
    request["child"] = MakeTreeInput(request["child"])
    request["child"]["output"]["path_name"] = str(output_path / "CohortChild.SLDPRT")
    request["child"]["document"].update(child)
    placed = [occurrence(spec) for spec in case["placements"]]
    names = [f"CohortChild-{index + 1}" for index in range(len(placed))]
    request["occurrences"] = [{"name": occurrence_name, "placement": pose} for occurrence_name, (pose, _) in zip(names, placed, strict=True)]
    encoded = json_bytes(request)
    program = root / "re/tooling/sw2026/AssemblyRootProcess.py"
    result = subprocess.run([sys.executable, "-I", "-B", str(program), str(root)], cwd=root, input=encoded, capture_output=True, check=False, timeout=120)
    if result.returncode:
        raise ValueError(result.stderr.decode())
    archived = json.loads(result.stdout)
    checks = ("reconstructed_bytes_identical", "maps_consistent", "manager_bytes_identical", "resolved_bytes_identical", "empty_mates_linked", "definition_bytes_identity", "directory_headers_agree")
    if archived["denied_reads"] or not all(archived[key] for key in checks):
        raise ValueError("generated assembly failed guarded archive checks")
    if (
        archived["component_total"] != len(names)
        or archived["configuration_component_total"] != len(names)
        or [entry["name"] for entry in archived["occurrences"]] != names
        or any(entry["child_configuration"]["f08"] != "Default" for entry in archived["occurrences"])
    ):
        raise ValueError("generated occurrences differ from authored placement order")
    parent = base64.b64decode(archived.pop("blob"), validate=True)
    child_record = archived["child"]
    part = base64.b64decode(child_record.pop("blob"), validate=True)
    if digest(part) != child_record["sha256"]:
        raise ValueError("generated child differs from its construction receipt")
    return {name + ".SLDASM": parent, "CohortChild.SLDPRT": part}, encoded, archived, names, [matrix for _, matrix in placed]


def verify_child(data, dimensions):
    from Classes import registry
    from RectangleReadback import read_rectangle
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from tests.Convert.Solidworks.Research.Composition.ProfileRoots import ReadLinkedRoots

    archive = SldprtArchive.from_bytes(data)
    model, roots = ReadLinkedRoots(archive, registry())
    classes = [node.cls for node in roots]
    if classes.count("moInkMarkupFolder_c") != 1 or "moNotesAreaFtrFolder_c" in classes:
        raise ValueError("generated child markup roles differ")
    observed = read_rectangle(archive=archive, model=model, profiles=roots)
    if [row["name"] for row in observed["values"]] != ["D1", "D2"] or observed["logical_types"] != [4, 5, 4, 5]:
        raise ValueError("generated child width and height ownership differs")
    for row in observed["values"]:
        if row["value_m"] != dimensions[row["name"] + "@Sketch1"] or not row["display_owns_sketch"]:
            raise ValueError("generated child dimension differs from its authored intent")
    return observed


def main():
    parser = argparse.ArgumentParser(description="Freeze dimensioned assembly candidates from authored neutral placements")
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--source-lock", type=Path, required=True)
    parser.add_argument("--specs", type=Path, required=True)
    parser.add_argument("--split", choices=("discovery", "heldout"), required=True)
    parser.add_argument("--guest-root", type=PureWindowsPath, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve(strict=True)
    lock = checked_json(args.source_lock, SOURCE_LOCK)
    specs_data = args.specs.read_bytes()
    if args.split == "heldout" and digest(specs_data) != lock["specs_sha256"]:
        raise ValueError("held-out neutral specification differs from its source lock")
    cases = [row for row in json.loads(specs_data)["cases"] if row["split"] == args.split and row["placements"]]
    expected = [row["name"] for row in lock["cases"] if row["split"] == args.split and row["name"] != "A12SyncedEmpty"]
    if [row["name"] for row in cases] != expected or not args.guest_root.is_absolute():
        raise ValueError("predicted cohort or encoded output location differs")

    def git(*command):
        return subprocess.check_output(["git", "-C", str(repo), *command])

    if git("rev-parse", WRITER + "^{tree}").strip().decode() != WRITER_TREE:
        raise ValueError("frozen writer tree differs")
    child, dimensions = authoring_child(git)
    args.output.mkdir(parents=True, exist_ok=False)
    specs = []
    with tempfile.TemporaryDirectory(prefix="kit-sw2026-dimensioned-source-") as directory:
        root = Path(directory).resolve()
        source_count = export_source(repo, git, root)
        sys.path[:0] = [str(root), str(root / "src"), str(root / "re/tooling/sw2026"), str(root / "re/tooling/sw2026/serial")]
        for case in cases:
            trials = []
            for label, parameter, value in EDITS:
                target = args.guest_root / "Inspection" / "Work" / case["name"] / label / "Generated"
                files, request, structural, names, matrices = compose_case(root, case, child, target)
                structural["child"]["structure"] = verify_child(files["CohortChild.SLDPRT"], dimensions)
                destination = args.output / "Generated" / case["name"] / label
                destination.mkdir(parents=True, exist_ok=False)
                current = dimensions | {parameter: value}
                trials.append({
                    "title": label, "parameter": parameter, "value_m": value,
                    "names": names, "expected_placement": matrices, "dimensions": current,
                    "geometry": geometry(current, edited=label),
                    "files": {name: write(destination / name, data) for name, data in files.items()},
                    "writer_request_sha256": write(destination / "WriterRequest.json", request),
                    "archive_checks_sha256": write(destination / "ArchiveChecks.json", json_bytes(structural)),
                })
            specs.append({"name": case["name"], "trials": trials})
    predictions = {
        "schema": "kit.sw2026.dimensioned-assembly-predictions.v1", "split": args.split,
        "generator_revision": WRITER, "generator_tree": WRITER_TREE, "source_lock_sha256": SOURCE_LOCK,
        "specs_sha256": digest(specs_data), "prediction_tool_sha256": digest(Path(__file__).read_bytes()),
        "geometry": geometry(dimensions), "dimensions": dimensions, "source_files": source_count, "cases": specs,
    }
    print(json.dumps({"predictions_sha256": write(args.output / "Predictions.json", json_bytes(predictions)), "case_count": len(specs)}))


if __name__ == "__main__":
    main()
