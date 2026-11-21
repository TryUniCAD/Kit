from argparse import ArgumentParser
from base64 import b64decode
from io import BytesIO
import json
import os
from pathlib import Path
from subprocess import run
import sys
from time import time
from zipfile import ZipFile

from ThinHeldoutPacket import (
    CASES, LOCK_SHA, MODES, SCHEMA, SPEC, SWROOT, THINROOT, WRITER, WRITER_TREE,
    archive_path, checked, digest, encode, packet_data, publish, require,
)


def writer_code(packet, manifest, root, *, extract):
    packed = checked(packet / "Code.zip", manifest["code_sha256"])
    code = root / "Code"
    with ZipFile(BytesIO(packed)) as archive:
        names = archive.namelist()
        require(len(names) == len({name.casefold() for name in names}), "ambiguous writer archive paths")
        require(all(not row.is_dir() and (row.external_attr >> 16) & 0o170000 in (0, 0o100000)
                    for row in archive.infolist()), "writer archive has non-file members")
        files = [(name, code.joinpath(*archive_path(name).parts)) for name in names]
        if extract:
            code.mkdir(parents=True)
        require(not code.is_symlink(), "guest writer closure is indirect")
        for name, path in files:
            raw = archive.read(name)
            require(path.resolve().is_relative_to(code.resolve()), "writer path escapes the private workspace")
            if extract:
                path.parent.mkdir(parents=True, exist_ok=True)
                publish(path, raw)
            checked(path, digest(raw))
        require(set(names) == {path.relative_to(code).as_posix() for path in code.rglob("*") if path.is_file()},
                "unexpected input or code in the frozen writer directory")
    return code


def locked_intents(code, lock):
    sys.path.insert(0, str(code / SWROOT))
    from RevolveFamilyModel import validate_specs

    spec = json.loads(checked(Path(SPEC), lock["spec_sha256"]))
    require((spec["family"], spec["split"]) == ("thin", "heldout"), "wrong locked neutral intent family")
    cases = validate_specs(spec)
    require(len(cases) == len(CASES) and {case["wall_mode"] for case in cases} == MODES,
            "pre-writer intent does not contain all four independent wall modes")
    return cases


def build_one(code, root, case, epoch):
    tool = code / THINROOT / "BuildThinControls.py"
    runner = ("from pathlib import Path; import runpy, sys; "
              "sys.path.insert(0, str(Path(sys.argv[1]).parent)); del sys.argv[0]; "
              "runpy.run_path(sys.argv[0], run_name='__main__')")
    destination = root / "Generated" / (case["name"] + ".SLDPRT")
    request = encode({"case": case, "destination": str(destination), "epoch": epoch})
    outputs = []
    for _ in range(2):
        process = run((sys.executable, "-I", "-B", "-c", runner, str(tool), "--worker"),
                      input=request, capture_output=True, cwd=root, check=False)
        if process.returncode:
            private = root / "PrivateFailures"
            private.mkdir(exist_ok=True)
            publish(private / (case["name"] + ".txt"), process.stderr)
            raise ValueError("frozen model-only writer refused this sealed intent")
        outputs.append(json.loads(process.stdout))
    a, b = outputs
    require(a == b and a["runtime_external_access_attempts"] == 0
            and len(a["typed_streams"]) == 10 and all(row["byte_identity"] for row in a["typed_streams"].values()),
            "isolated writer proof, repeat bytes or linked stream parity differ")
    raw = b64decode(a.pop("candidate"), validate=True)
    require((digest(raw), len(raw)) == (a["sha256"], a["bytes"]), "frozen worker output differs")
    return destination, raw, {"candidate_sha256": a["sha256"], "candidate_bytes": a["bytes"],
                              "typed_streams": len(a["typed_streams"]), "repeat_bytes_equal": True,
                              "writer_runtime_external_access_attempts": 0}


def prepare(packet, pin, manifest, lock, root):
    require(not root.exists(), "use a fresh private guest evaluation root")
    code = writer_code(packet, manifest, root, extract=True)
    cases = locked_intents(code, lock)
    require(all(case["plane"] == "front" and not case["reverse"] for case in cases),
            "sealed cohort exceeds the measured forward Front-only frozen writer")
    epoch = int(manifest["frozen_at"])
    candidates = [build_one(code, root, case, epoch) for case in cases]
    (root / "Generated").mkdir()
    rows = {}
    for slot, (path, raw, row) in zip(CASES, candidates, strict=True):
        require(publish(path, raw) == row["candidate_sha256"], "staged candidate differs from isolated generation")
        rows[slot] = row
    require(digest(checked(Path(SPEC), lock["spec_sha256"])) == lock["spec_sha256"], "neutral intent changed")
    report = {"schema": SCHEMA, "freeze_sha256": pin, "source_lock_sha256": LOCK_SHA,
              "writer_revision": WRITER, "writer_src_tree": WRITER_TREE, "spec_sha256": lock["spec_sha256"],
              "writer_epoch": epoch, "generated_at": time(), "cases": rows,
              "writer_processes": 2 * len(rows), "original_native_files_read_during_generation": 0,
              "writer_runtime_external_access_attempts": 0, "native_acceptance": False}
    return {"passed": True, "generation_sha256": publish(root / "Generation.json", encode(report)),
            "generated_slots": len(rows), "native_acceptance": False}


def native(packet, pin, generation_pin, manifest, lock, root):
    code = writer_code(packet, manifest, root, extract=False)
    generation = json.loads(checked(root / "Generation.json", generation_pin))
    require(generation["schema"] == SCHEMA and generation["freeze_sha256"] == pin
            and generation["source_lock_sha256"] == LOCK_SHA and generation["writer_revision"] == WRITER
            and generation["writer_src_tree"] == WRITER_TREE and generation["spec_sha256"] == lock["spec_sha256"]
            and generation["writer_epoch"] == int(manifest["frozen_at"]) <= generation["generated_at"]
            and generation["original_native_files_read_during_generation"] == 0
            and generation["writer_runtime_external_access_attempts"] == 0 and generation["writer_processes"] == 8
            and generation["native_acceptance"] is False and tuple(generation["cases"]) == CASES,
            "candidate generation receipt identity differs")
    cases = locked_intents(code, lock)
    sys.path.insert(0, str(code / THINROOT))
    from ThinHeldoutNative import run_native

    return run_native(packet, pin, generation_pin, lock, root, cases, generation)


def main():
    parser = ArgumentParser(description="Run sealed neutral generation or a separately approved native comparison")
    parser.add_argument("action", choices=("prepare", "native"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--pin", required=True)
    parser.add_argument("--generation-pin")
    args = parser.parse_args()
    require(os.name == "nt" and sys.version_info[:2] == (3, 12), "use the designated Windows Python 3.12")
    packet = args.packet.resolve(strict=True)
    root = None
    try:
        manifest, lock, root = packet_data(packet, args.pin)
        if args.action == "prepare":
            result = prepare(packet, args.pin, manifest, lock, root)
        else:
            require(args.generation_pin is not None, "native phase requires the exact generation receipt pin")
            result = native(packet, args.pin, args.generation_pin, manifest, lock, root)
    except Exception as error:
        if root is not None and root.is_dir():
            path = root / ("Private" + args.action.capitalize() + "Failure.json")
            if not path.exists():
                publish(path, encode({"error": repr(error)}))
        message = "sealed cohort exceeds the measured forward Front-only frozen writer"
        reason = "frozen_orientation_unsupported" if str(error) == message else "private_" + args.action + "_failure"
        result = {"passed": False, "failure": reason, "error_type": type(error).__name__}
    print(encode(result).decode(), end="")
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
