from argparse import ArgumentParser
from base64 import b64decode
from hashlib import sha256
from pathlib import Path, PureWindowsPath
from subprocess import run
import json
import sys


ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
TOOLS = ("InspectCircleSketch.py", "AuthorCurves.py", "Swapp.py", "InspectFresh.py", "OracleIdentity.py")


def write(directory, name, data):
    with (directory / name).open("xb") as handle:
        handle.write(data)
    return sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def checked_source(src, manifest, name):
    key = "re/tooling/sw2026/" + name
    data = (src / key).read_bytes()
    if sha256(data).hexdigest() != manifest["files_sha256"][key]:
        raise ValueError("frozen source differs: " + key)
    return data


def replay(src, proof, action, request):
    result = run([sys.executable, "-I", "-B", str(proof), str(src), action],
                 input=request, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace"))
    report = json.loads(result.stdout)
    if report["passed"] is not True or report["runtime_input_file_reads"] != 0 or report["sdk_runtime_research_imports"] != 0:
        raise ValueError("guarded worker did not prove SDK-only construction")
    return report


def case(src, proof, source, out, guest):
    data = source.read_bytes()
    request = json.loads(data)
    built = replay(src, proof, "build", data)
    prepared = replay(src, proof, "prepare", encoded({**request, "build": built}))
    dimensions = built["dimensions"]
    kind = dimensions["mode"]
    name = dimensions["name"]
    stored = PureWindowsPath(built["stored_self_path"])
    if (dimensions != prepared["dimensions"] or kind not in ("radius", "diameter")
            or stored.parent != PureWindowsPath(r"C:\KitSdkCandidates")
            or stored.name != name + ".SLDPRT"):
        raise ValueError("candidate provenance, names or driving intent differ")
    if prepared["artifact"] != {key: built[key] for key in ("bytes", "sha256")}:
        raise ValueError("build and preparation did not inspect the same bytes")
    if len(built["streams"]) != 10 or prepared["exact_repacked_archive"] is not True:
        raise ValueError("incomplete generated native archive")
    child = out / source.stem
    child.mkdir()
    blob = b64decode(built.pop("blob"), validate=True)
    candidate = child / stored.name
    if len(blob) != built["bytes"] or write(child, candidate.name, blob) != built["sha256"]:
        raise ValueError("generated file hash or size differs")
    evidence = {
        "request_sha256": write(child, "Request.json", data),
        "build_sha256": write(child, "Build.json", encoded(built)),
        "prepare_sha256": write(child, "Prepare.json", encoded(prepared)),
        "candidate_sha256": built["sha256"],
        "stored_self_path": str(stored),
    }
    geometry = {
        "name": name, "configuration_name": dimensions["config"],
        "sketch_name": dimensions["sketch"], "extrusion_name": dimensions["feature"],
        "origin_name": "Origin", "plane_axis": dimensions["plane_axis"], "profile_kind": "circle", "feature_kind": "extrusion",
        "center_m": dimensions["center_m"], "radius_m": dimensions["radius_m"], "depth_m": dimensions["depth_m"],
        "circle_dimension": {"mode": kind, "fix_center": True},
        "expected_body_density_kg_m3": 1.0, "document_density_kg_m3": 1000.0,
        "end_condition": dimensions["end_condition"], "reverse_direction": dimensions["reverse_direction"],
    }
    oracle_case = {"name": name, "path": guest(candidate), "sha256": built["sha256"],
                   "request": {"document": geometry}, "edit_factor": request["radial_edit_factor"],
                   "depth_edit_factor": request["depth_edit_factor"]}
    if dimensions["second_depth_m"] is not None:
        geometry["reverse_depth_m"] = dimensions["second_depth_m"]
        oracle_case["reverse_depth_edit_factor"] = request["second_edit_factor"]
    return oracle_case, evidence


def main():
    parser = ArgumentParser()
    parser.add_argument("frozen_source", type=Path)
    parser.add_argument("request_directory", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("control", type=Path)
    parser.add_argument("--control-sha256", required=True)
    parser.add_argument("--shared-home", type=Path, required=True)
    parser.add_argument("--case", action="append")
    args = parser.parse_args()
    base = args.frozen_source.resolve(strict=True)
    request_dir = args.request_directory.resolve(strict=True)
    out = args.output.resolve()
    share = args.shared_home.resolve(strict=True)
    src = base / "Kit"
    raw_manifest = (base / "FrozenSource.json").read_bytes()
    manifest = json.loads(raw_manifest)
    proof = src / "re/tooling/sw2026/SdkCircleProof.py"
    checked_source(src, manifest, proof.name)
    origin = Path(__file__).resolve().parents[3]
    if out.is_relative_to(origin) or out.is_relative_to(base):
        raise ValueError("oracle output must be outside both executable source trees")

    def guest(path):
        return "//Mac/Home/" + path.resolve().relative_to(share).as_posix()

    guest(out)
    out.mkdir(parents=True, exist_ok=False)
    cases = []
    receipts = {}
    labels = args.case or ["radius", "diameter"]
    if any(not label or not label.isascii() or not label.replace("-", "").isalnum() for label in labels):
        raise ValueError("oracle case labels must be simple local request stems")
    for label in labels:
        row, receipt = case(src, proof, request_dir / (label + ".json"), out, guest)
        cases.append(row)
        receipts[label] = receipt
    if any(len({row[key] for row in cases}) != len(cases) for key in ("sha256", "name")):
        raise ValueError("distinct circle designs require distinct files and names")
    control = args.control.resolve(strict=True)
    if sha256(control.read_bytes()).hexdigest() != args.control_sha256:
        raise ValueError("native control does not match the approved immutable hash")
    tools = out / "Tools"
    tools.mkdir()
    tool_hashes = {name: write(tools, name, checked_source(src, manifest, name)) for name in TOOLS}
    job = {
        "schema": "kit.sw2026.sdk-circle-oracle-job.v1", "source_revision": manifest["base"],
        "checkout_root": guest(origin), "output": guest(out / "Inspection"),
        "control": guest(control), "control_sha256": args.control_sha256, "oracle_sha256": ORACLE,
        "generator": {"frozen_source_sha256": sha256(raw_manifest).hexdigest(),
                      "source_count": manifest["file_count"], "tools": tool_hashes, "cases": receipts,
                      "packet_preparer_sha256": sha256(Path(__file__).read_bytes()).hexdigest()},
        "cases": cases,
    }
    result = write(out, "InspectionJob.json", encoded(job))
    print(json.dumps({"packet_sha256": result, "cases": receipts, "tools": tool_hashes}, sort_keys=True))


if __name__ == "__main__":
    main()
