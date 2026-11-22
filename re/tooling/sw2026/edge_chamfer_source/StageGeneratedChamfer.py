from argparse import ArgumentParser
from base64 import b64decode
from math import degrees, dist, isclose
from pathlib import Path
from subprocess import check_output
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(HERE.parent), str(HERE.parent.parent / "edge_fillet_source")]

from ChamferModel import predict, validate_spec, values_si
from ChamferPacket import TOOLS, write_new
from FilletPacket import BUILD, CONTROL, ORACLE
from ProveChamferEdgeOwners import canonical, composed_requests, digest, invoke, require
from RunNativeChamferProbe import OUTPUT, PACKET, SCHEMA, verified


def candidate_plan(request, index):
    shape = request["shape"]
    axis = shape["edge_axis"]
    transverse = [item for item in range(3) if item != axis]
    angle = degrees(shape["angle_rad"])
    case = {"name": request["case"], "center_mm": [0.0, 0.0], "size_mm": list(request["size_mm"]),
            "edge_axis": "xyz"[axis], "corner": {"xyz"[int(key)]: ("min", "max")[value]
                                                for key, value in shape["corner"].items()},
            "distance_mm": shape["distance_m"] * 1000, "angle_deg": angle,
            "edit": {"distance_mm": 6.125} if index == 0 else {"angle_deg": 62.625}}
    return case, [transverse.index(shape["distance_axis"]), "tan"]


def stage(output, control):
    require(output.is_absolute() and not output.exists() and not output.resolve().is_relative_to(ROOT)
            and output.name == PACKET.name, "stage an unused, disclosed external Packet folder")
    revision = check_output(("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip()
    committed = check_output(("git", "status", "--porcelain", "--untracked-files=no"), cwd=ROOT, text=True)
    require(not committed, "freeze the source revision before constructing trial bytes")
    control_bytes = control.read_bytes()
    require(digest(control_bytes) == CONTROL, "control differs from the healthy native fixture")
    requests = tuple(composed_requests())
    designs = tuple(candidate_plan(request, index) for index, request in enumerate(requests))
    spec = {"schema": "kit.sw2026.edge-chamfer-source-spec.v1", "cohort": "disclosed",
            "cases": [case for case, _ in designs]}
    validate_spec(spec)
    assets = {"Control.SLDPRT": control_bytes}
    baselines = []
    for request, (case, branch) in zip(requests, designs, strict=True):
        data = canonical(request)
        first, second = (invoke("--model", "--deliver", data=data) for _ in range(2))
        require(first == second, "standalone worker did not reproduce the exact candidate")
        proof = json.loads(first)
        blob = b64decode(proof.pop("model_bytes"), validate=True)
        require(proof["container_sha256"] == digest(blob) and proof["bytes"] == len(blob)
                and proof["intent_sha256"] == digest(data) and proof["guarded_runtime_reads"] == 0,
                "guarded writer and native packet candidate differ")
        want = predict(case, values_si(case, False), branch)
        require(all(dist(one, two) <= 1e-12 for one, two in zip(proof["selected_endpoints_m"], want["source_edge"], strict=True))
                and all(isclose(a, b, rel_tol=0.0, abs_tol=1e-16)
                        for a, b in zip(values_si(case, False), (request["shape"]["distance_m"], request["shape"]["angle_rad"]), strict=True)),
                "independent COM expectations differ from the actual writer intent")
        raw_path = f"Candidates/{case['name']}.SLDPRT"
        require(str(PACKET / raw_path) == request["locator"], "candidate's encoded self locator differs from native test path")
        assets[raw_path] = blob
        baselines.append({"path": raw_path, "locator": request["locator"], "archive_sha256": digest(blob),
                          "branch": branch, "writer_proof": proof})
    for folder, names in TOOLS.items():
        for name in names:
            assets[f"Tool/{name}"] = (ROOT / folder / name).read_bytes()
    assets["Tool/RunNativeChamferProbe.py"] = HERE.with_name("RunNativeChamferProbe.py").read_bytes()
    manifest = {"schema": SCHEMA, "oracle_build": BUILD, "oracle_sha256": ORACLE, "construction_revision": revision,
                "guest_packet": str(PACKET), "guest_output": str(OUTPUT), "spec": spec, "cases": baselines,
                "guarded_generation_processes": 4, "guarded_runtime_reads": 0, "heldout_inputs_read": 0,
                "files": {name: {"bytes": len(data), "sha256": digest(data)} for name, data in assets.items()}}
    output.mkdir(parents=True)
    for name, data in assets.items():
        path = output / name
        path.parent.mkdir(exist_ok=True)
        with path.open("xb") as sink:
            sink.write(data)
    manifest_file = output / "Trial.json"
    write_new(manifest_file, manifest)
    pin = digest(manifest_file.read_bytes())
    verified(manifest_file, pin)
    return {"manifest_sha256": pin, "files": len(assets), "candidates": {row["path"]: row["archive_sha256"] for row in baselines}}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--control", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(stage(args.output, args.control), sort_keys=True))
