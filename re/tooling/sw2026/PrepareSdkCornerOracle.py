from __future__ import annotations

import argparse
from base64 import b64decode
from hashlib import sha256
import json
from pathlib import Path
from shutil import copyfile
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--writer-manifest", type=Path, required=True)
    parser.add_argument("--closure", type=Path, required=True)
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    sys.path.insert(0, str(root / "re/tooling/sw2026"))
    from InspectSdkBlindPart import tree_prediction
    from InspectSdkCorner import SCHEMA, TOOLS
    from AuthorRectangleAnchors import CONTROL, ORACLE

    def digest(path):
        return sha256(path.read_bytes()).hexdigest()

    def write(name, value):
        path = args.output / name
        path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")
        return path

    if args.output.exists():
        raise ValueError("choose an unused native corner packet")
    result = json.loads((args.replay / "Result.json").read_bytes())
    if not result["passed"] or result["processes"] != 12 or result["heldout_inputs_read"] or result["fcstd_conversion_accepted"]:
        raise ValueError("expected the exact source-only three-design guarded replay")
    if digest(args.control) != CONTROL:
        raise ValueError("pristine L1 native control differs")
    label = "F14aSizedDiscovery"
    row, = [row for row in result["designs"] if row["name"] == label]
    files = {"Request.json": (label + "Request.json", "request_sha256"),
             "Build.json": (label + "Build.json", "build_sha256"),
             "Repeat.json": (label + "Repeat.json", "repeat_sha256"),
             "Prepare.json": (label + "Prepare.json", "prepare_sha256"),
             "Counterpart.json": (label + "Counterpart.json", "counterpart_sha256"),
             "Candidate.SLDPRT": (label + ".SLDPRT", "candidate_sha256")}
    for source, key in files.values():
        if digest(args.replay / source) != row[key]:
            raise ValueError("guarded replay input changed: " + source)
    args.output.mkdir(parents=True)
    for target, (source, _) in files.items():
        copyfile(args.replay / source, args.output / target)
    for target, source in (("WriterManifest.json", args.writer_manifest), ("FrozenSource.json", args.closure), ("Control.SLDPRT", args.control)):
        copyfile(source, args.output / target)
    request = json.loads((args.output / "Request.json").read_bytes())
    build = json.loads((args.output / "Build.json").read_bytes())
    if b64decode(build["blob"], validate=True) != (args.output / "Candidate.SLDPRT").read_bytes():
        raise ValueError("candidate does not match the actual repeated SDK emission")
    document = request["document"]
    profile = document["sketches"]["$tuple"][0]["name"]
    feature = document["feature_timeline"]["$tuple"][0]["name"]
    names = ["D1@" + profile, "D2@" + profile, "D1@" + feature]
    dimensions = dict(zip(names, (build["vertices_m"][1][0], build["vertices_m"][2][1], build["depth_m"]), strict=True))
    edits = [{"parameter": name, "value_m": value, "expected_dimensions_m": dimensions | {name: value}}
             for name, value in zip(names, (0.026125, 0.018875, 0.015625), strict=True)]
    case = {"model_name": build["name"], "self_path": build["native_path"], "profile": profile, "feature": feature,
            "origin": request["settings"]["system"]["origin_name"], "parameter_names": names, "dimensions_m": dimensions,
            "configuration_name": document["configurations"]["$tuple"][0]["name"],
            "support": document["support_planes"]["$tuple"][0]["name"], "density_kg_m3": request["settings"]["density_kg_m3"],
            "vertices_m": build["vertices_m"], "depth_m": build["depth_m"], "edits": edits,
            "synthetic_size_match_only": True, "fcstd_conversion_accepted": False}
    case["tree"] = tree_prediction(request, {"intent": {"profile": profile, "feature": feature, "resolved_roots": 19}})
    write("Case.json", case)
    tools = args.output / "Tools"
    tools.mkdir()
    for name in sorted(TOOLS):
        copyfile(root / "re/tooling/sw2026" / name, tools / name)
    inputs = {path.name: digest(path) for path in sorted(args.output.iterdir()) if path.is_file()}
    job = {"schema": SCHEMA, "oracle_sha256": ORACLE, "control_sha256": CONTROL, "heldout_inputs_read": 0,
           "fcstd_conversion_accepted": False, "inputs_sha256": inputs,
           "tools_sha256": {path.name: digest(path) for path in sorted(tools.iterdir())}}
    packet = write("Packet.json", job)
    print(json.dumps({"packet": str(packet), "sha256": digest(packet), "native_processes_started": 0,
                      "expected_native_processes": 8, "candidate_sha256": build["sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
