import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys


FILES = {
    "Native/Source/PerpendicularFrontTop.SLDASM": "54303798c1386b050dd80544c0394f85fd2c56e6bd306d70f8d1d188b5aed5ef",
    "Native/Source/PerpendicularDatum.SLDPRT": "14c79efaae814f6d4802fba9ebeafaf463685ab1754b1469d9313b60384d36f8",
    "Native/Edited/PerpendicularFrontTop.SLDASM": "0005da6fc1eaa1421fd264b17e455015b332912092698fdf54f4437960c391af",
    "Native/Edited/PerpendicularDatum.SLDPRT": "3fc915e7bb9210d542c1d19564b73abadcb0aed336511ed094549c10db6fb40d",
    "SavedAuthor.json": "0d0783ba55f61d192e30b317a54def4784a0941ed4e6e63561e6f9e92bf9fbcd",
}
PROGRESS = {
    "before": "7db0a2ab5843dc9fe783d94be75f8163afac9ca0ff4fbbaf23aa97875802c5a3",
    "author": "de6b9d76aa80edcfa3b6dc62a8cc170f73ad02f700c4836678e39bd8cfff9c16",
    "reopen-source": "91f2056b7621941a19414bbea8197ccd2558969574d0717b51d1ebab948f5b45",
    "reopen-edited": "ca53dd376e2f7215d7661db028e5249b6f41180a09c67f8fbbd5dd13a00330df",
    "after": "17d29c93f7ea9dbac8d859631e6441de6a688719c00b2a6a6a04a9657d403671",
    "lock": "790993adaca4d876db3e3574d7bded68e3474ca937b57f1101283933a073f584",
}
TOOLS = ("CheckPerpendicularReader.py", "AuditPerpendicularReader.py", "PreparePerpendicularReadFaults.py",
         "PublicMateReadProcess.py", "SdkMatesProcess.py", "CollectPerpendicularReadEvidence.py",
         "CollectPerpendicularEvidence.py", "CollectDrawingViewSupportEvidence.py")


def digest(data):
    return sha256(data).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def source_manifest(root):
    return {path.relative_to(root).as_posix(): digest(path.read_bytes()) for path in sorted((root / "src").rglob("*.py"))}


def pinned(path, expected):
    data = path.read_bytes()
    require(digest(data) == expected, "a declared disclosed source or observation changed: " + path.name)
    return data


def execute(script, root, request=None, extra=()):
    result = subprocess.run([sys.executable, "-I", "-B", str(Path(__file__).with_name(script)), "--root", str(root), *extra],
                            input=None if request is None else json.dumps(request), text=True, capture_output=True, timeout=90, check=False)
    return {"exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def read_public(root, path, deferred=False):
    request = {"path": str(path)}
    if deferred:
        request["adapter_values"] = {"resolve_components": False}
    return execute("PublicMateReadProcess.py", root, request)


def signature(result):
    if result["exit_code"]:
        return {"exit_code": result["exit_code"], "error": result["stderr"].strip().splitlines()[-1]}
    return {"exit_code": 0, "json_sha256": digest(result["stdout"].encode())}


def custody(packet):
    case = packet / "Disclosed/D01"
    for name, expected in FILES.items():
        pinned(case / name, expected)
    rows, identities = [], []
    for phase, expected in PROGRESS.items():
        value = json.loads(pinned(packet / "Progress/D01" / phase / "Record.json", expected))
        require(value["passed"] and value["stage"] == "passed" and value["phase"] == phase
                and value["writer_output_count"] == 0
                and value["packet_sha256"] == "9fdfff4ee0fc960dbb70ec3058d4ac6652ba5413caf7171aa119d5b4500b4a41",
                "the disclosed source phase did not pass")
        if phase != "lock":
            identity = value["identity"]
            require(identity["file_version"] == "34.5.2.0604"
                    and identity["sha256"] == "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe",
                    "the disclosed native process build is not exact")
            identities.append((identity["process_id"], identity["process_creation_filetime"]))
        rows.append({"phase": phase, "record_sha256": expected})
    lock = json.loads((packet / "Progress/D01/lock/Record.json").read_bytes())
    require(lock["source_locked"] and lock["heldout_source_locked"] is False, "the allowed source is not a disclosed source lock")
    require(len(set(identities)) == 5, "the disclosed source phase process identities are not independent")
    return {"source_packet_sha256": "9fdfff4ee0fc960dbb70ec3058d4ac6652ba5413caf7171aa119d5b4500b4a41",
            "artifacts": dict(FILES), "phases": rows, "native_process_creation_identities": identities, "disclosed_only": True}


def audit_cases(root, packet, output):
    sys.path.insert(0, str(root / "src"))
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    source = packet / "Disclosed/D01"
    native = json.loads((source / "SavedAuthor.json").read_bytes())
    rows = []
    for label in ("Source", "Edited"):
        parent = source / "Native" / label / "PerpendicularFrontTop.SLDASM"
        child = parent.with_name("PerpendicularDatum.SLDPRT")
        blob = SldprtArchive.from_bytes(parent.read_bytes()).require("Contents/Config-0-MatesList")
        request = {"path": str(parent), "sha256": digest(parent.read_bytes()), "bytes": parent.stat().st_size,
                   "stream_sha256": digest(blob), "child_path": str(child), "child_sha256": digest(child.read_bytes()), "expected": native[label.lower()]}
        actual = execute("AuditPerpendicularReader.py", root, request)
        require(actual["exit_code"] == 0, "disclosed perpendicular audit failed: " + actual["stderr"][-2500:])
        value = json.loads(actual["stdout"])
        require(value["passed"] and not value["codec"]["usage"]["read"]["native_byte_fields"], "the perpendicular graph has unclassified bytes")
        (output / (label + "Audit.json")).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        rows.append({"case": label, **value})
        print(json.dumps({"case": label, "public_and_linked_codec": "passed"}), flush=True)
    return rows


def compare_legacy(root, baseline, cohort):
    declared = json.loads(cohort.read_bytes())["files"]
    require(len(declared) == 12, "the six disclosed ordinary pairs differ")
    for row in declared:
        require(len(pinned(Path(row["path"]), row["sha256"])) == row["bytes"], "declared cohort size differs")
    rows, process_count = [], 0
    for item in declared:
        path = Path(item["path"])
        for deferred in ((False, True) if path.suffix.upper() == ".SLDASM" else (False,)):
            before, after = (read_public(code, path, deferred) for code in (baseline, root))
            process_count += 2
            require(signature(before) == signature(after), "legacy public document or deferred behavior changed: " + path.name)
            require(deferred or before["exit_code"] == 0, "the prior normal read was not successful")
            rows.append({"file_sha256": item["sha256"], "deferred": deferred, "exact_result_equal": True, **signature(after)})
    return rows, process_count


def codec_regression(root, cohort, linked):
    manifest = json.loads(cohort.read_bytes())
    previous = json.loads(linked.read_bytes())
    expected = {row["file_sha256"]: row for row in previous["files"]}
    cases = [row for row in manifest["files"] if Path(row["path"]).suffix.upper() == ".SLDASM"]
    require(previous["passed"] and len(cases) == previous["stream_count"] == 6, "the original linked codec proof does not qualify")
    rows = []
    for item in cases:
        request = {**item, "stream_sha256": expected[item["sha256"]]["stream_sha256"]}
        actual = execute("SdkMatesProcess.py", root, request, ("--worker",))
        require(actual["exit_code"] == 0, "ordinary linked codec regression failed: " + actual["stderr"][-1500:])
        value = json.loads(actual["stdout"])
        require(all(value[key] == expected[item["sha256"]][key] for key in ("stream_bytes", "map_base", "map_terminal", "mate_count", "byte_identity")),
                "the ordinary linked map or wire identity changed")
        rows.append(value)
    return rows


def negative_cases(root, packet, output):
    parent = packet / "Disclosed/D01/Native/Source/PerpendicularFrontTop.SLDASM"
    child = parent.with_name("PerpendicularDatum.SLDPRT")
    prepared = execute("PreparePerpendicularReadFaults.py", root, extra=("--parent", str(parent), "--child", str(child), "--output", str(output / "DiagnosticInputs")))
    require(prepared["exit_code"] == 0, "diagnostic source preparation failed: " + prepared["stderr"][-2000:])
    manifest = json.loads((output / "DiagnosticInputs/Faults.json").read_bytes())
    rows = []
    for item in manifest["cases"]:
        actual = read_public(root, Path(item["path"]))
        if actual["exit_code"] == 0:
            sys.path.insert(0, str(root / "src"))
            from interchange import CadDocument

            document = CadDocument.from_json(actual["stdout"])
            typed = document.metadata.get("solidworks.typed_mates_semantics", {})
            require(typed.get("status") == ("admitted" if item["case"] == "RepackedControl" else "unsupported"),
                    "a diagnostic graph was silently admitted: " + item["case"])
            outcome = {"status": typed.get("status"), "diagnostic": typed.get("diagnostic"),
                       "full_selected_mate_graph": typed.get("full_selected_mate_graph")}
        else:
            require(item["case"] != "RepackedControl", "unmodified repacked reader control failed")
            outcome = {"status": "format_error", **signature(actual)}
        rows.append({"case": item["case"], "diagnostic_file_sha256": item["sha256"], **outcome})
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--baseline-root", type=Path, required=True)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--cohort", type=Path, required=True)
    parser.add_argument("--linked-proof", type=Path, required=True)
    parser.add_argument("--bindings", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "reader proof needs a new output directory")
    root, baseline = args.root.resolve(), args.baseline_root.resolve()
    current_sources, baseline_sources = source_manifest(root), source_manifest(baseline)
    tool_sources = {name: digest(Path(__file__).with_name(name).read_bytes()) for name in TOOLS}
    source_bytes = (json.dumps({"current": current_sources, "baseline": baseline_sources, "tools": tool_sources}, indent=2, sort_keys=True) + "\n").encode()
    disclosed = custody(args.packet)
    args.output.mkdir(parents=True)
    (args.output / "SourceManifest.json").write_bytes(source_bytes)
    cases = audit_cases(root, args.packet, args.output)
    legacy, legacy_processes = compare_legacy(root, baseline, args.cohort)
    ordinary_codecs = codec_regression(root, args.cohort, args.linked_proof)
    extra = []
    for label in ("Source", "Edited"):
        parent = args.packet / "Disclosed/D01/Native" / label / "PerpendicularFrontTop.SLDASM"
        for target, deferred in ((parent.with_name("PerpendicularDatum.SLDPRT"), False), (parent, True)):
            first, second = (read_public(code, target, deferred) for code in (baseline, root))
            require(signature(first) == signature(second), "existing child or deferred perpendicular behavior changed")
            extra.append({"case": label, "child_read": not deferred, "exact_result_equal": True, **signature(second)})
    negatives = negative_cases(root, args.packet, args.output)
    require(source_manifest(root) == current_sources and source_manifest(baseline) == baseline_sources
            and tool_sources == {name: digest(Path(__file__).with_name(name).read_bytes()) for name in TOOLS}, "proof sources changed during execution")
    require(custody(args.packet) == disclosed, "disclosed source custody changed during proof")
    result = {"schema": "kit.sw2026.perpendicular-reader-process-proof.v1", "passed": True,
              "source_manifest_sha256": digest(source_bytes), "bindings_sha256": digest(args.bindings.read_bytes()),
              "disclosed_custody": disclosed, "cases": cases, "ordinary_codec_regressions": ordinary_codecs,
              "legacy_public_regressions": legacy, "child_and_deferred_regressions": extra,
              "diagnostic_results": negatives, "diagnostic_negative_count": len(negatives) - 1,
              "process_count": len(cases) + legacy_processes + len(ordinary_codecs) + 2 * len(extra) + len(negatives) + 1,
              "writer_output_count": 0, "diagnostic_output_count": len(negatives), "native_processes_started": 0,
              "heldout_inputs_read": False, "source_inputs_unchanged": True,
              "public_registration_changed": False, "private_sdk_overlay_only": True,
              "native_generated_perpendicular_acceptance": False, "full_family_coverage": False}
    data = (json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    (args.output / "ReaderResults.json").write_bytes(data)
    print(json.dumps({"passed": True, "process_count": result["process_count"], "diagnostic_negatives": len(negatives) - 1,
                      "result_sha256": digest(data)}, sort_keys=True))


if __name__ == "__main__":
    main()
