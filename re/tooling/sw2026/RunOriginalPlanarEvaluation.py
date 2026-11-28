import argparse
from base64 import b64decode
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from AuthorCurves import digest, require, write_json
from OriginalPlanarEvaluation import SCHEMA, SLOTS, SOURCE_SPECS, checked, verify


def progress(path, slot, stage, status, **fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, {"schema": "kit.sw2026.original-planar-public-progress.v1", "slot": slot, "stage": stage,
                      "status": status, "worker_pid": os.getpid(), "recorded_at": time.time(), **fields})


def write_frozen(path, value):
    require(not path.exists(), "preserve the existing original-evaluation evidence")
    write_json(path, value)
    return digest(path)


def execute(source_root, output, entry, name, incoming=None, extra=()):
    args = [sys.executable, "-I", "-B", str(source_root / "re/tooling/sw2026" / entry), *extra]
    data = None if incoming is None else json.dumps(incoming, separators=(",", ":"), allow_nan=False).encode()
    with subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
        try:
            stdout, stderr = process.communicate(data, timeout=180)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
        identity = {"stdout_sha256": sha256(stdout).hexdigest(), "stderr_sha256": sha256(stderr).hexdigest(), "worker_pid": process.pid, "exit_code": process.returncode}
    (output / (name + ".stdout")).write_bytes(stdout)
    (output / (name + ".stderr")).write_bytes(stderr)
    require(identity["exit_code"] == 0, "the private source/recipe SDK stage failed: " + name)
    value = json.loads(stdout)
    require(value.get("passed", True) and not value.get("runtime_input_file_reads") and not value.get("com_imports"), "the private SDK process crossed its declared boundary")
    require("worker_pid" not in value or value["worker_pid"] == identity["worker_pid"], "the independently observed SDK worker identity differs")
    return value, identity


def dependency_check(packet, wanted):
    _, _, _, source_root, _ = verify(packet, wanted)
    sys.path[:0] = [str(source_root), str(source_root / "src"), str(source_root / "re/tooling/sw2026")]
    from convert import open_document
    from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.MakePlanarGroup import MakePlanarGroup
    from convert.adapters.solidworks.Archive.Construction.Part.MakeRectDimPart import MakeRectDimPart
    from interchange import CadDocument
    from OriginalPlanarRecipe import dimensioned_child
    from SdkAssemblySettings import assembly_settings
    from SdkBlindPartSettings import settings

    require(not any(name == "Swapp" or name == "pythoncom" or name.startswith("win32com") for name in sys.modules), "the no-source dependency preflight imported CAD automation")
    import zlib

    return {"passed": True, "heldout_inputs_read": 0, "native_processes_started": 0, "interpreter": sys.version,
            "interpreter_sha256": digest(Path(sys.executable)), "zlib_build": zlib.ZLIB_VERSION, "zlib_runtime": zlib.ZLIB_RUNTIME_VERSION}


def prepare(packet, wanted, slot, progress_path, released):
    require(released and os.name == "nt", "only an explicitly released guest stage may expose an original source")
    job, locators, rows, source_root, _ = verify(packet, wanted)
    target = Path(locators["private_guest_root"]) / slot
    require(not target.exists(), "the original slot already has private evidence; preserve it and freeze a separately rooted retry")
    target.mkdir(parents=True)
    marker = target / "Failure.json"
    progress(progress_path, slot, "dependency_preflight", "running")
    try:
        dependency = dependency_check(packet, wanted)
        dependency_hash = write_frozen(target / "DependencyReceipt.json", dependency)
        progress(progress_path, slot, "source_custody", "running", dependency_receipt_sha256=dependency_hash)
        locked = rows[SLOTS[slot]]
        locator = locators["slots"][slot]
        specs_path = checked(Path(locators["specs_guest_path"]), SOURCE_SPECS)
        specs = json.loads(specs_path.read_bytes())
        require(specs["schema"] == "kit.sw2026.ordinary-assembly-specs.v1" and len(specs["cases"]) == len({row["name"] for row in specs["cases"]}) == 5 and [row["split"] for row in specs["cases"]] == ["discovery"] * 3 + ["heldout"] * 2 and bool(specs.get("synchronize_owned_children")), "the original pre-writer author recipe envelope differs")
        case, = [row for row in specs["cases"] if row["name"] == SLOTS[slot] and row["split"] == "heldout"]
        parent = checked(Path(locator["parent_guest_path"]), locked["native_sha256"])
        child = checked(Path(locator["child_guest_path"]), locked["synchronized_child"]["native_sha256"])
        custody = {"source_specs_sha256": SOURCE_SPECS, "source_parent_sha256": locked["native_sha256"], "source_child_sha256": locked["synchronized_child"]["native_sha256"]}
        write_json(target / "SourceCustody.json", custody)
        progress(progress_path, slot, "source_sdk_read", "running")
        source, source_id = execute(source_root, target, "ReadSdkPlanarGroupNative.py", "SourceRead", extra=("read", "--root", str(source_root), "--file", str(parent)))
        require(source["input_sha256"] == locked["native_sha256"], "the public source reader opened a different original")
        source_data = json.loads(source["document_json"])
        require(source_data["assembly"]["documents"]["$tuple"][0]["document"]["source"]["sha256"] == locked["synchronized_child"]["native_sha256"], "the public source reader resolved a different actual child")
        working = target / "GeneratedInput"
        paths = {"assembly_path": str(working / (case["name"] + ".SLDASM")), "child_path": str(working / "CohortChild.SLDPRT")}
        progress(progress_path, slot, "authored_semantic_projection", "running")
        semantic, semantic_id = execute(source_root, target, "OriginalPlanarProcess.py", "Semantic", {"document_json": source["document_json"], "case": case, "dimensions_m": [.04, .02, .01], "output": paths}, ("--root", str(source_root)))
        from CheckOriginalPlanarMethod import leaves, no_recorded_state

        require(all(type(value) is str for value in leaves(semantic["names"])), "the source projection contains non-name captured state")
        no_recorded_state(semantic["request"])
        request_hash = write_frozen(target / "NeutralRequest.json", semantic["request"])
        prediction_hash = write_frozen(target / "Prediction.json", semantic["prediction"])
        names_hash = write_frozen(target / "AuthoredNames.json", semantic["names"])
        freeze_hash = write_frozen(target / "RequestFreeze.json", {"schema": "kit.sw2026.original-planar-prebuild-freeze.v1", "request_sha256": request_hash,
                                 "prediction_sha256": prediction_hash, "names_sha256": names_hash, "constructor_invocations": 0,
                                 "method_source_manifest_sha256": job["method_source_manifest_sha256"], "native_processes_started": 0})
        progress(progress_path, slot, "guarded_sdk_construction", "running", request_freeze_sha256=freeze_hash)
        first, first_id = execute(source_root, target, "SdkPlanarGroupProcess.py", "BuildA", semantic["request"], (str(source_root),))
        again, again_id = execute(source_root, target, "SdkPlanarGroupProcess.py", "BuildB", semantic["request"], (str(source_root),))
        a, b = dict(first), dict(again)
        require(a.pop("worker_pid") != b.pop("worker_pid") and a == b, "the sealed SDK construction is not deterministic across fresh guarded processes")
        counterpart, counterpart_id = execute(source_root, target, "SdkAssemblyCounterpart.py", "Counterpart", {"request": semantic["request"], "build": first}, (str(source_root),))
        require(counterpart["same_as_independent_research"], "the full recipe-generated files differ from the independent mathematical composer")
        frozen = target / "FrozenGenerated"
        frozen.mkdir()
        files = {}
        for kind, name in (("assembly", case["name"] + ".SLDASM"), ("child", "CohortChild.SLDPRT")):
            payload = b64decode(first[kind]["blob"], validate=True)
            (frozen / name).write_bytes(payload)
            require(digest(frozen / name) == first[kind]["sha256"], "the frozen generated file differs from the guarded construction")
            files[kind] = {"file": name, "sha256": first[kind]["sha256"], "bytes": len(payload), "encoded_path": str(working / name)}
        sys.path[:0] = [str(source_root), str(source_root / "src")]
        from interchange import CadDocument
        from ReadSdkPlanarGroupNative import compare

        source_comparison = compare(CadDocument.from_json(source["document_json"]), semantic["prediction"], False, locked["synchronized_child"]["native_sha256"])
        public, public_id = execute(source_root, target, "ReadSdkPlanarGroupNative.py", "FrozenPublicRead", extra=("read", "--root", str(source_root), "--file", str(frozen / files["assembly"]["file"])))
        generated_comparison = compare(CadDocument.from_json(public["document_json"]), semantic["prediction"], False, files["child"]["sha256"])
        audits = {}
        for kind in ("assembly", "child"):
            audited, identity = execute(source_root, target, "ReadSdkPlanarGroupNative.py", "FrozenAudit" + kind, extra=("audit", "--root", str(source_root), "--file", str(frozen / files[kind]["file"])))
            audits[kind] = {"result": audited, "identity": identity}
        verify(packet, wanted)
        checked(parent, locked["native_sha256"])
        checked(child, locked["synchronized_child"]["native_sha256"])
        record = {"schema": "kit.sw2026.original-planar-prepared-slot.v1", "slot": slot, "evaluation_sha256": wanted,
                  "source": {"parent": str(parent), "parent_sha256": locked["native_sha256"], "child": str(child), "child_sha256": locked["synchronized_child"]["native_sha256"]},
                  "request_sha256": request_hash, "prediction_sha256": prediction_hash, "names_sha256": names_hash, "request_freeze_sha256": freeze_hash,
                  "generated_files": files, "processes": {"source": source_id, "semantic": semantic_id, "first": first_id, "again": again_id, "counterpart": counterpart_id, "public": public_id},
                  "dependency_receipt_sha256": dependency_hash,
                  "source_public_comparison": source_comparison, "generated_public_comparison": generated_comparison, "frozen_audits": audits,
                  "typed_stream_round_trips": first["round_trips"] + again["round_trips"], "runtime_input_file_reads_during_projection_and_construction": 0,
                  "source_native_payload_or_cache_values_forwarded": False, "native_processes_started": 0, "heldout_source_exposed": True, "heldout_slots_evaluated": 1, "native_acceptance": False, "passed": True}
        stage = target / "StagePacket.json"
        write_json(stage, record)
        progress(progress_path, slot, "prepared", "passed", stage_packet_sha256=digest(stage), generated_sha256={key: row["sha256"] for key, row in files.items()})
        return {"slot": slot, "passed": True, "stage_packet_sha256": digest(stage), "native_processes_started": 0}
    except Exception as error:
        write_json(marker, {"error": repr(error), "passed": False, "native_acceptance": False})
        progress(progress_path, slot, "prepare", "failed", error_type=type(error).__name__, private_failure_sha256=digest(marker))
        raise RuntimeError("private original-evaluation preparation failed; inspect the guest-private evidence") from None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("verify", "dependency-check", "prepare", "measure"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--slot", choices=tuple(SLOTS))
    parser.add_argument("--stage-sha256")
    parser.add_argument("--progress", type=Path)
    parser.add_argument("--release-source-evaluation", action="store_true")
    args = parser.parse_args()
    packet = args.packet.resolve(strict=True)
    if args.command == "verify":
        verify(packet, args.packet_sha256)
        result = {"passed": True, "heldout_inputs_read": 0, "native_processes_started": 0}
    elif args.command == "dependency-check":
        result = dependency_check(packet, args.packet_sha256)
    else:
        require(args.slot is not None and args.progress is not None, "the released guest stage requires an opaque slot and public progress path")
        if args.command == "prepare":
            result = prepare(packet, args.packet_sha256, args.slot, args.progress, args.release_source_evaluation)
        else:
            require(args.stage_sha256 and args.release_source_evaluation and os.name == "nt", "native measurement requires the exact prepared stage and explicit source release")
            from InspectOriginalPlanarSlot import run

            result = run(packet, args.packet_sha256, args.slot, args.stage_sha256, args.progress)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
