from __future__ import annotations

import argparse
from base64 import b64decode
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import re
from shutil import copyfile
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from AuthorCurves import digest, require, write_json
from InspectGeneratedReferencePlane import ORACLE, SCHEMA, SOURCE_LOCK_SHA256, TOOLS, predict
from ReferencePlaneSourcePlan import disclosed_cases


SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[3]
SOURCE_PACKET_SHA256 = "db56b95bad3543b5949848ce263bc8865c578ead20b688166d0b576310eeda7a"
CORRELATION_SHA256 = "e57aa3912b10f038421e83e433f0cfb9015e1676949ae902cea61bc2b3ec10ce"
WRITER_FILES = ("re/tooling/sw2026/builders/Part.py", "re/tooling/sw2026/builders/Radial.py",
                "re/tooling/sw2026/builders/ReferencePlane.py", "re/tooling/sw2026/ReferencePlanePartProcess.py")


def pinned(path, sha):
    require(path.is_absolute() and path.resolve(strict=True) == path and not path.is_symlink() and digest(path) == sha,
            "the declared private source changed or is not canonical")
    return json.loads(path.read_bytes())


def prepare(args):
    root = args.output.absolute()
    build, source = args.build.resolve(strict=True), args.source.resolve(strict=True)
    require(root.parent.resolve(strict=True) == root.parent and not root.exists() and not root.is_relative_to(ROOT),
            "choose an unused private native plane packet outside the checkout")
    require(re.fullmatch(r"[0-9a-f]{40}", args.writer_revision), "bind the actual committed writer revision")
    guest = PureWindowsPath(args.guest_root)
    require(guest.is_absolute() and guest.drive.startswith("\\\\") and ".." not in guest.parts, "declare the exact mounted guest packet root")
    lock_path = ROOT / "re/solidworks/v2026/heldout/ReferencePlaneSourceLock01.json"
    lock = pinned(lock_path, SOURCE_LOCK_SHA256)
    require(lock["distinct_native_processes"] == 18 and lock["heldout_writer_acceptance"] is False and
            all(next(row for row in lock["records"] if row["case_id"] == slot and row["phase"] == "lock")["heldout_source_locked"]
                for slot in ("H01", "H02")), "pre-writer native source locks are incomplete")
    packet = pinned(source / "Source.json", SOURCE_PACKET_SHA256)
    api_path = source / "ApiMetadata.json"
    require(packet["oracle_sha256"] == ORACLE, "source oracle identity differs")
    expected_api, = (row["api_metadata_sha256"] for row in lock["records"] if row["phase"] == "metadata")
    require(api_path.resolve(strict=True) == api_path and not api_path.is_symlink() and digest(api_path) == expected_api,
            "source API metadata differs from its pre-writer lock")
    correlation = pinned(ROOT / "re/solidworks/measurements/2026/ReferencePlaneOffsetCorpusCorrelation01.json", CORRELATION_SHA256)
    control_row, = (row for row in correlation["cases"] if row["case_id"] == "D01")
    control_file = source / "Disclosed/D01/Native/FrontOffsetCircle.SLDPRT"
    control_identity = control_row["siblings"]["source"]
    require(control_file.resolve(strict=True) == control_file and not control_file.is_symlink(), "disclosed control custody escaped")
    require(control_row["passed"] and control_row["source_qualification"]["healthy_brackets"] and
            digest(control_file) == control_identity["sha256"] and control_file.stat().st_size == control_identity["bytes"],
            "the disclosed control is not its exact qualified source")
    proof = json.loads((build / "CompositionProof.json").read_bytes())
    require(proof["passed"] and proof["source_lock_sha256"] == SOURCE_LOCK_SHA256 and proof["heldout_inputs_read"] == 0,
            "guarded composition prerequisite is incomplete")
    manifest = pinned(build / "CodeManifest.json", proof["code_manifest_sha256"])
    for name, expected in manifest["files_sha256"].items():
        relative = Path(name)
        require(not relative.is_absolute() and ".." not in relative.parts and
                (build / "CodeRoot" / relative).resolve(strict=True) == build / "CodeRoot" / relative and
                digest(build / "CodeRoot" / relative) == expected, "frozen writer code closure changed")
    for name in WRITER_FILES:
        require(digest(ROOT / name) == manifest["files_sha256"][name] == proof["changed_writer_files_sha256"][name],
                "the staged writer differs from its guarded frozen generator")
    generated_row, = (row for row in proof["generated_cases"] if row["case_id"] == "G01")
    request_path = build / "G01Request.json"
    request = pinned(request_path, generated_row["request_sha256"])
    report_path = build / "G01Build0.stdout"
    report = json.loads(report_path.read_bytes())
    artifact = report["native"]
    payload = b64decode(artifact["artifact_base64"], validate=True)
    require(artifact["sha256"] == generated_row["native_sha256"] == sha256(payload).hexdigest()
            and len(payload) == artifact["bytes"] == generated_row["native_bytes"] and
            report["native_acceptance"] is False and report["heldout_inputs_tested"] == report["input_runtime_file_access_attempts"] == 0,
            "the candidate differs from its guarded generated artifact")
    prediction = predict(request, args.edit_distance_m)
    filename = request["document"]["name"] + ".SLDPRT"
    require(PureWindowsPath(request["output"]["path_name"]) == guest / "GeneratedInput" / filename,
            "actual guest candidate path must match the generator's encoded file identity")
    control_case, = (row for row in disclosed_cases() if row["id"] == "D01")
    control_request = deepcopy(request)
    control_request["document"].update(name=control_case["name"], configuration_name="Default", plane_axis="z", radius_m=control_case["radius_m"],
                                       depth_m=control_case["depth_m"], sketch_name="PlaneSketch", extrusion_name="PlaneBoss", origin_name="Origin")
    control_request["presentation"]["plane_names"] = {"x": "Right Plane", "y": "Top Plane", "z": "Front Plane"}
    control_request["offset_plane_discovery"] = {"name": "OffsetPlane", "distance_m": control_case["distance_m"], "reverse": control_case["reverse"]}
    root.mkdir()
    for directory in ("Tools", "Controls", "FrozenGenerated", "GeneratedInput"):
        (root / directory).mkdir()
    copyfile(control_file, root / "Controls" / control_file.name)
    copyfile(lock_path, root / "SourceLock.json")
    copyfile(api_path, root / "ApiMetadata.json")
    copyfile(request_path, root / "Request.json")
    copyfile(build / "CodeManifest.json", root / "CodeManifest.json")
    for directory in ("FrozenGenerated", "GeneratedInput"):
        (root / directory / filename).write_bytes(payload)
    tools = {}
    for name in TOOLS:
        origin = source / "Tools" / name if name in packet["tools_sha256"] else SCRIPT.parent / name
        require(origin.resolve(strict=True) == origin and not origin.is_symlink(), "native tool custody escaped")
        if name in packet["tools_sha256"]:
            require(digest(origin) == packet["tools_sha256"][name], "qualified native source helper changed")
        copyfile(origin, root / "Tools" / name)
        tools[name] = digest(root / "Tools" / name)
    job = {"schema": SCHEMA, "oracle_sha256": ORACLE, "source_lock_sha256": SOURCE_LOCK_SHA256,
           "source_packet_sha256": SOURCE_PACKET_SHA256, "source_correlation_sha256": CORRELATION_SHA256,
           "writer_revision": args.writer_revision, "writer_files_sha256": proof["changed_writer_files_sha256"],
           "code_manifest_sha256": proof["code_manifest_sha256"], "composition_proof_sha256": digest(build / "CompositionProof.json"),
           "generator_report_sha256": digest(report_path), "preparer_sha256": digest(SCRIPT), "tool_hashes": tools,
           "api_metadata_sha256": digest(root / "ApiMetadata.json"), "guest_root": str(guest),
           "control": {"filename": control_file.name, "sha256": control_identity["sha256"], "bytes": control_identity["bytes"],
                       "prediction": predict(control_request, control_case["edit_distance_m"])},
           "generated": {"filename": filename, "sha256": artifact["sha256"], "bytes": artifact["bytes"],
                         "request_sha256": digest(request_path), "edit_distance_m": args.edit_distance_m, "prediction": prediction},
           "heldout_inputs_tested": 0, "native_acceptance": False}
    path = root / "Trial.json"
    write_json(path, job)
    identity = digest(path)
    outcome = subprocess.run([sys.executable, "-I", "-B", str(root / "Tools/InspectGeneratedReferencePlane.py"), "verify", str(path),
                              "--packet-sha256", identity], capture_output=True, check=False)
    require(outcome.returncode == 0, "frozen native observer verification failed: " + outcome.stderr.decode())
    return {"packet": str(path), "packet_sha256": identity, "observer_sha256": tools["InspectGeneratedReferencePlane.py"],
            "writer_files_sha256": job["writer_files_sha256"], "candidate_sha256": artifact["sha256"], "native_processes_started": 0}


def main():
    parser = argparse.ArgumentParser()
    for name in ("build", "source", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--guest-root", required=True)
    parser.add_argument("--writer-revision", required=True)
    parser.add_argument("--edit-distance-m", required=True, type=float)
    print(json.dumps(prepare(parser.parse_args()), sort_keys=True))


if __name__ == "__main__":
    main()
