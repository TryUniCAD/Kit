from __future__ import annotations

import argparse
import json
import subprocess
import sys
from base64 import b64decode
from pathlib import Path, PureWindowsPath

ROOT = Path(__file__).resolve().parents[3]
TOOLS = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "src"), str(TOOLS / "serial")]

from CheckDrawingDefinitions import SOURCE_LOCK, checked_artifacts, digest, require
from DrawingCacheCases import CONTROL, NATIVE_NAME
from InspectBlankDrawing import CASE_NAMES, INPUT_KINDS, TOOL_NAMES, TRIAL_SCHEMA, input_path, read_packet
from builders.DrawingSheet import drawing_sheet
from convert.adapters.solidworks.Container.Container import EmitSldprt, SldprtArchive, TemplateFields


def _generated_case(spec, windows_path):
    filename = spec["name"] + ".SLDDRW"
    require(PureWindowsPath(windows_path).is_absolute() and PureWindowsPath(windows_path).name == filename,
            "generated drawing identity must name its exact staged Windows file")
    request = {**spec, "output": {"path_name": windows_path, "saved_at": spec["provenance"]["modified_at"]}}
    request_bytes = (json.dumps(request, sort_keys=True, indent=2) + "\n").encode()
    generated = subprocess.run(
        [sys.executable, "-B", str(TOOLS / "DrawingRootProcess.py")], cwd=ROOT,
        input=request_bytes, capture_output=True, timeout=60,
    )
    require(generated.returncode == 0, generated.stderr.decode("utf-8", errors="replace"))
    report = json.loads(generated.stdout)
    artifact = b64decode(report.pop("artifact_base64"), validate=True)
    require(report["native_acceptance"] is False and report["input_runtime_file_access_attempts"] == 0,
            "generated drawing needs a source-only construction receipt")
    require(report["native_sha256"] == digest(artifact) and report["native_bytes"] == len(artifact), "generated drawing bytes differ from report")
    streams = SldprtArchive.from_bytes(artifact).streams
    require(report["streams"] == {name: {"bytes": len(data), "sha256": digest(data)} for name, data in streams.items()},
            "generated drawing stream identities differ from report")
    return filename, artifact, streams, report, request_bytes


def _expected_generated(spec):
    sheet = drawing_sheet(spec["sheet"])
    expected = {"sheet": sheet.name, "sheet_properties": [sheet.native_paper_code, 13, sheet.scale_numerator,
                sheet.scale_denominator, 0, *sheet.dimensions, 1], "view": None, "whats_wrong": 0}
    folders, names = spec["folder_names"], spec["sheet_names"]
    tree = [[folders[key], kind, None] for key, kind in (
        ("comments", "CommentsFolder"), ("blocks", "BlockFolder"), ("binder", "DocsFolder"),
        ("annotations", "DetailCabinet"), ("ink_markups", "InkMarkupFolder"), ("review_markups", "MarkupCommentFolder"),
    )]
    tree.append([sheet.name, "DrSheet", None])
    tree.extend([names[key], kind, sheet.name] for key, kind in (
        ("plane_name", "RefPlane"), ("profile_name", "ProfileFeature"), ("detail_name", "DetailFolder"),
    ))
    return expected, tree


def prepare(*, corpus, spec_path, output, windows_path):
    output = output.resolve()
    require(not output.is_relative_to(ROOT) and not output.exists(), "blank drawing trial needs an unused directory outside the checkout")
    spec_bytes = spec_path.read_bytes()
    spec = json.loads(spec_bytes)
    filename, artifact, generated, report, request_bytes = _generated_case(spec, windows_path)
    lock_bytes = SOURCE_LOCK.read_bytes()
    lock = json.loads(lock_bytes)
    control = next(case for case in lock["cases"] if case["name"] == CONTROL and case["split"] == "discovery")
    native, control_state, _ = checked_artifacts(corpus, control)
    require(control_state["view"] is None, "declared blank drawing control has a model view")
    archive = SldprtArchive.from_bytes(native)
    require(archive.format_version == 4 and generated.keys() <= archive.streams.keys(), "unexpected native control stream inventory")
    signatures, type_ids = TemplateFields(native, archive)
    subset = {name: data for name, data in archive.streams.items() if name in generated}
    require(len(subset) < len(archive.streams), "native reduction must omit additional streams")
    repacked, reduced = (EmitSldprt(list(streams.items()), archive.file_id, archive.format_version, signatures, type_ids)
                         for streams in (archive.streams, subset))
    require(SldprtArchive.from_bytes(repacked).streams == archive.streams and SldprtArchive.from_bytes(reduced).streams == subset,
            "repacking changed a retained native logical stream")
    expected, tree = _expected_generated(spec)
    payloads = (native, repacked, reduced, artifact)
    stream_sets = (archive.streams, archive.streams, subset, generated)
    rows = []
    for name, kind, data, streams in zip(CASE_NAMES, INPUT_KINDS, payloads, stream_sets, strict=True):
        constructed = kind == "generated"
        row = {"name": name, "kind": kind, "filename": filename if constructed else NATIVE_NAME,
               "bytes": len(data), "sha256": digest(data), "streams": sorted(streams), "expected": expected if constructed else control_state}
        if constructed:
            row["expected_tree"] = tree
        dest = input_path(output, row)
        dest.parent.mkdir(parents=True, exist_ok=False)
        dest.write_bytes(data)
        rows.append(row)
    tools = output / "Tools"
    tools.mkdir(exist_ok=False)
    tool_hashes = {}
    for tool in TOOL_NAMES:
        code = (TOOLS / tool).read_bytes()
        (tools / tool).write_bytes(code)
        tool_hashes[tool] = digest(code)
    (output / "GeneratedRequest.json").write_bytes(request_bytes)
    (output / "GeneratedConstruction.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    packet = {"schema": TRIAL_SCHEMA, "native_acceptance": False, "source_lock_sha256": digest(lock_bytes),
              "control_sha256": digest(native), "oracle_sha256": lock["oracle_sha256"], "generator_input_sha256": digest(request_bytes),
              "authored_spec_sha256": digest(spec_bytes), "tool_hashes": tool_hashes, "cases": rows}
    require(checked_artifacts(corpus, control)[0] == native, "locked D00 source changed while staging trial")
    manifest = output / "Trial.json"
    payload = (json.dumps(packet, sort_keys=True, indent=2) + "\n").encode()
    manifest.write_bytes(payload)
    verification = subprocess.run(
        [sys.executable, "-B", "-c", "from InspectBlankDrawing import read_packet; from pathlib import Path; import sys; read_packet(Path(sys.argv[1]), sys.argv[2])",
         str(manifest), digest(payload)], cwd=tools, capture_output=True, check=True, timeout=20,
    )
    require(not verification.stdout, "unexpected blank drawing packet verification output")
    return manifest, digest(payload), packet


def main():
    parser = argparse.ArgumentParser(description="Stage a private generated blank drawing and paired native controls")
    parser.add_argument("corpus", type=Path)
    parser.add_argument("spec", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--windows-path", required=True)
    args = parser.parse_args()
    manifest, sha256, packet = prepare(corpus=args.corpus, spec_path=args.spec, output=args.output, windows_path=args.windows_path)
    print(json.dumps({"manifest": str(manifest), "sha256": sha256, "case_hashes": {row["name"]: row["sha256"] for row in packet["cases"]},
                      "tool_hashes": packet["tool_hashes"]}, sort_keys=True))


if __name__ == "__main__":
    main()
