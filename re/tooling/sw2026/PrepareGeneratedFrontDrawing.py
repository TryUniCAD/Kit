from __future__ import annotations

import argparse
import json
import subprocess
import sys
from base64 import b64decode
from pathlib import Path, PureWindowsPath
from shutil import copyfile

ROOT = Path(__file__).resolve().parents[3]
TOOLS = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "src"), str(TOOLS / "serial")]

from CheckDrawingDefinitions import SOURCE_LOCK, check_header, checked_artifacts, compare_sheet, digest, reencode, require
from Classes import registry
from InspectGeneratedFrontDrawing import INPUT_NAMES, SCHEMA, TOOL_NAMES, input_files
from PrepareBlankDrawing import _expected_generated as expected_blank_sheet
from PrepareFrontDrawingMap import PART_FILE, diagnostic_variants
from convert.adapters.solidworks.Container.Container import EmitSldprt, SldprtArchive, TemplateFields


DISCLOSED = "D01FrontView"
OMISSION = ROOT / "re/solidworks/measurements/2026/DrawingFrontDetailingMapOmission01.json"


def encode_json(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def file_summary(name, payload):
    return {"filename": name, "bytes": len(payload), "sha256": digest(payload)}


def generated_inputs(request, windows_directory):
    drawing, part = request["drawing"], request["part"]
    directory = PureWindowsPath(windows_directory)
    require(directory.is_absolute() and directory.name == INPUT_NAMES[-1], "specify the exact absolute Windows GeneratedInput directory")
    filenames = (drawing["name"] + ".SLDDRW", part["document"]["name"] + ".SLDPRT")
    for model, name in zip((drawing, part), filenames, strict=True):
        require(PureWindowsPath(name).name == name, "generated file stem must be a single path component")
        model["output"] = {**model["output"], "path_name": str(directory / name)}
    data = encode_json(request)
    command = [sys.executable, "-B", str(TOOLS / "DrawingFrontBundleProcess.py")]
    ordered = [subprocess.run(command, cwd=ROOT, input=data, capture_output=True, timeout=60) for _ in range(2)]
    for result in ordered:
        require(result.returncode == 0, result.stderr.decode("utf-8", errors="replace"))
    require(ordered[0].stdout == ordered[1].stdout, "generated front drawing package replay differs")
    report = json.loads(ordered[0].stdout)
    require(report["native_acceptance"] is False and report["input_runtime_file_access_attempts"] == 0,
            "generated front drawing requires a source-only guarded build")
    payloads = []
    for key, name in zip(("drawing", "part"), filenames, strict=True):
        item = report[key]
        payload = b64decode(item.pop("artifact_base64"), validate=True)
        require((digest(payload), len(payload)) == (item["sha256"], item["bytes"]), f"generated {name} file digest differs")
        require(item["streams"] == {role: {"bytes": len(raw), "sha256": digest(raw)}
                                    for role, raw in SldprtArchive.from_bytes(payload).streams.items()}, "generated logical stream hashes differ")
        payloads.append(payload)
    return filenames, payloads, report, data


def expected_generated(request):
    spec, part, view = request["drawing"], request["part"], request["view"]
    expected, tree = expected_blank_sheet(spec)
    document = part["document"]
    xs, ys = zip(*document["vertices_m"])
    length, width, depth = max(xs) - min(xs), max(ys) - min(ys), document["depth_m"]
    center = [(max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, depth / 2]
    x, y = view["position"]
    margin = min(expected["sheet_properties"][5:7]) * 0.02
    low_x, low_y, high_x, high_y = x - length / 2 - margin, y - width / 2 - margin, x + length / 2 + margin, y + width / 2 + margin
    name = view["name"]
    expected["view"] = {
        "name": name, "orientation": view["orientation"], "position_m": [x, y], "scale": view["scale"],
        "resolved_reference_path": part["output"]["path_name"], "configuration": document["configuration_name"],
        "outline_m": [low_x, low_y, high_x, high_y], "model_to_view": [1, 0, 0, 0, 1, 0, 0, 0, 1, x-center[0], y-center[1], -center[2], 1, 0, 0, 0],
        "child_volume_m3": length * width * depth, "child_area_m2": 2 * (length * width + length * depth + width * depth),
        "child_center_m": center,
    }
    tree.append([name, "AbsoluteView", expected["sheet"]])
    tree.extend([view["supports"][key], kind, name] for key, kind in (
        ("detail", "DetailFolder"), ("sheet_plane", "RefPlane"), ("sheet_profile", "ProfileFeature"),
        ("model_plane", "RefPlane"), ("model_profile", "ProfileFeature"),
    ))
    return expected, tree


def native_control(corpus, stream_roles, lock):
    case, = [item for item in lock["cases"] if item["name"] == DISCLOSED and item["split"] == "discovery"]
    native, saved, reopened = checked_artifacts(corpus, case)
    child = (corpus / DISCLOSED / "author" / PART_FILE).read_bytes()
    require(digest(child) == lock["reference_part_sha256"], "disclosed front control part differs from its lock")
    rules = registry()
    (_, _, omitted), _ = diagnostic_variants(native, saved, reopened, rules)
    archive = SldprtArchive.from_bytes(native)
    omitted_archive = SldprtArchive.from_bytes(omitted)
    require(stream_roles <= omitted_archive.streams.keys(), "disclosed control lacks a generated file role")
    signatures, entries = TemplateFields(native, archive)
    retained = {role: raw for role, raw in omitted_archive.streams.items() if role in stream_roles}
    reduced = EmitSldprt(list(retained.items()), archive.file_id, archive.format_version, signatures, entries)
    repacked = SldprtArchive.from_bytes(reduced)
    require(repacked.streams == retained, "native reduction changed a retained logical stream")
    model, _ = reencode(repacked.require("Contents/Definition"), rules, repacked)
    header, _ = check_header(repacked.require("Header2"), rules)
    compare_sheet(model, header, saved, reopened)
    require(not model["n1578"], "native reduction changed its verified detailing omission")
    return native, reduced, child, saved, sorted(archive.streams)


def prepare(corpus, spec_path, output, windows_directory):
    output = output.resolve()
    require(not output.is_relative_to(ROOT) and not output.exists(), "choose an unused drawing trial directory outside the checkout")
    request = json.loads(spec_path.read_bytes())
    filenames, generated, report, request_bytes = generated_inputs(request, windows_directory)
    layout, tree = expected_generated(request)
    role_set = report["drawing"]["streams"].keys()
    lock_data, omission_data = SOURCE_LOCK.read_bytes(), OMISSION.read_bytes()
    lock, omission = json.loads(lock_data), json.loads(omission_data)
    require(omission["passed"] and omission["source_lock_sha256"] == digest(lock_data) and omission["oracle_sha256"] == lock["oracle_sha256"],
            "resolved view cache omission requires its independently qualified native result")
    native, reduced, child, saved, native_roles = native_control(corpus, role_set, lock)
    discovery_pair = (DISCLOSED + ".SLDDRW", PART_FILE)
    rows = []
    for name, names, payloads, roles, expected in zip(INPUT_NAMES, (discovery_pair, discovery_pair, filenames),
            ((native, child), (reduced, child), generated), (native_roles, sorted(role_set), sorted(role_set)), (saved, saved, layout), strict=True):
        row = {"name": name, "stream_roles": roles, "expected": expected,
               **{key: file_summary(filename, data) for key, filename, data in zip(("drawing", "part"), names, payloads, strict=True)}}
        if name == INPUT_NAMES[-1]:
            row["tree"] = tree
        for target, data in zip(input_files(output, row), payloads, strict=True):
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        rows.append(row)
    request_path = output / "GeneratedRequest.json"
    request_path.write_bytes(request_bytes)
    (output / "GeneratedConstruction.json").write_bytes(encode_json(report))
    guest = output / "Tools"
    guest.mkdir(exist_ok=False)
    for name in TOOL_NAMES:
        copyfile(TOOLS / name, guest / name)
    tools = encode_json({name: digest((guest / name).read_bytes()) for name in TOOL_NAMES})
    (guest / "GuestTools.json").write_bytes(tools)
    job = {"schema": SCHEMA, "native_acceptance": False, "writer_output_count": 2, "oracle_sha256": lock["oracle_sha256"],
           "source_lock_sha256": digest(lock_data), "omission_receipt_sha256": digest(omission_data),
           "generated_request_sha256": digest(request_bytes), "inputs": rows}
    packet = output / "PrivateManifest.json"
    packet_data = encode_json(job)
    packet.write_bytes(packet_data)
    packet_sha, tools_sha = digest(packet_data), digest(tools)
    subprocess.run([sys.executable, "-B", str(guest / "InspectGeneratedFrontDrawing.py"), str(packet),
                    "--packet-sha256", packet_sha, "--tools-sha256", tools_sha, "--verify-only"], check=True, timeout=30)
    return {"packet": str(packet), "packet_sha256": packet_sha, "tools_sha256": tools_sha,
            "inputs": [{key: row[key] for key in ("name", "drawing", "part")} for row in rows]}


def main():
    parser = argparse.ArgumentParser(description="Stage a guarded generated front drawing and separate disclosed native controls")
    for argument in ("corpus", "spec", "output"):
        parser.add_argument(argument, type=Path)
    parser.add_argument("--windows-directory", required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.corpus, args.spec, args.output, args.windows_directory), sort_keys=True))


if __name__ == "__main__":
    main()
