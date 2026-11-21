from argparse import ArgumentParser
from pathlib import Path
from subprocess import PIPE, run
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "EndModes"))

from AuditRevEndOwners import (
    ArchiveNode, ReadNativeLink, ReadRevOwners, SldprtArchive, audit_streams, digest,
    guard_runtime, require,
)
from ThinWireOwners import REF_CLASSES, RADIUS_CLASS, THIN_FEATURE, THIN_SPEC, inspect_thin
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.CheckBodyMut import CheckBodyMut
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Resolved.MakeResolvedCtx import MakeResolvedCtx
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut

SOURCE_LOCK = "f851a26cc549433b5a342b2b7801171f56e356b50866b7f84929353966d6fe25"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
VERSION = "34.5.2.0604"
CASES = {"ThinOne": 0, "ThinOpposite": 1, "ThinMidplane": 2, "ThinUnequal": 3}
PHASE_FILES = {"author": ".author.json", "reopen": ".reopen.json", "edited-reopen": "-edited.edited-reopen.json"}
ARCHIVE = "src/convert/adapters/solidworks/Archive"
LAYOUTS = ARCHIVE + "/Bodies/Layouts/Resolved"
LAYOUT_NAMES = ("DimensionFields", "ReferenceFields", "ResolvedSchemas", "ResolvedVirtuals", "RevolveFields")


def checked_bytes(path, sha):
    raw = path.read_bytes()
    require(digest(raw) == sha, "disclosed input digest differs")
    return raw


def receipt(path, sha):
    result = json.loads(checked_bytes(path, sha))
    identity = result["oracle_identity"]
    require(identity["sha256"] == ORACLE and identity["file_version"] == VERSION,
            "native phase has a different executable build")
    return result


def load_lock(capture):
    lock = json.loads(checked_bytes(capture / "SourceLock.json", SOURCE_LOCK))
    require(lock["passed"] and lock["split"] == "discovery" and lock["family"] == "thin"
            and lock["oracle_sha256"] == ORACLE and lock["oracle_build"] == VERSION
            and lock["fresh_processes"] == lock["distinct_processes"] == 14
            and lock["wall_side_consistent"] and lock["measured_first_wall_signs"] == [1]
            and lock["inputs_unchanged"] and lock["tools_unchanged"] and lock["idle_after"]
            and not lock["heldout_writer_acceptance"] and not lock["writer_output_count"],
            "expected the successful disclosed native thin authoring lock")
    rows = {row["case"]: row for row in lock["sources"]}
    require(tuple(rows) == tuple(CASES) and len(lock["sources"]) == len(rows),
            "disclosed thin case inventory changed")
    return lock, rows


def phase(capture, case, phase_row):
    name = phase_row["phase"]
    result = receipt(capture / case / (case + PHASE_FILES[name]), phase_row["sha256"])
    job = result["job"]
    require(job["case"]["name"] == case and job["phase"] == name and phase_row["passed"] and result["passed"]
            and result["first_failure"] is None and result["source_immutable"] and result["inspection_completed"]
            and not any(result[field] for field in ("controller_diagnostics", "dialogs", "cleanup_errors")),
            "native phase lost its successful original outcome")
    require(len(result["checks"]) == phase_row["checks"] == phase_row["checks_passed"]
            and all(row["passed"] for row in result["checks"]), "native numerical check inventory differs")
    if name != "author":
        require(result["open_status"] == {"opened": True, "errors": 0, "warnings": 0}
                and result["before_explicit_rebuild"]["whats_wrong"] == 0
                and result["before_explicit_rebuild"]["bodies"] == 1, "saved native source reopened with diagnostics")
    return result


def input_case(capture, row, is_edited):
    case = row["case"]
    phases = {p["phase"]: phase(capture, case, p) for p in row["phases"]}
    require(row["passed"] and tuple(phases) == tuple(PHASE_FILES), "native phase custody differs")
    original, reopened, derivative = (phases[name] for name in PHASE_FILES)
    save = reopened["edited_derivative"]
    roles = ("angle", "wall1", "wall2") if CASES[case] == 3 else ("angle", "wall1")
    require(original["native_sha256"] == row["native_sha256"] and original["native_bytes"] == row["native_bytes"]
            and save["save_status"] == [True, 0, 0] and reopened["edit"]["passed"]
            and [r["role"] for r in reopened["edit"]["dimensions"]] == list(roles),
            "native author, source and edited lifecycle did not stay linked")
    state = derivative["reopened"] if is_edited else reopened["reopened"]
    require(state["definition"]["wall_mode"] == CASES[case] and tuple(state["drivers"]) == roles,
            "native phase exposes a different driver inventory")
    sha, size = (save["sha256"], save["bytes"]) if is_edited else (row["native_sha256"], row["native_bytes"])
    asset = case + ("-edited" if is_edited else "") + ".SLDPRT"
    raw = checked_bytes(capture / case / asset, sha)
    require(len(raw) == size, "disclosed native source length differs")
    return raw, sha, state


def refusal(action, text, error_type=ValueError):
    try:
        action()
    except error_type as error:
        require(text in str(error), "wrong archive refusal: " + str(error))
        return str(error)
    raise ValueError("unqualified archive state was admitted")


def check_guards(archive, link):
    config, resolved = link.ConfigValue, link.ResolvedValue
    context = MakeResolvedCtx(19000, config.MapValue, resolved.ContextValue, None)
    result = {"unsupported_document_version": refusal(
        lambda: ReadResolvedMut(archive.require(link.StreamName), 18999, config.MapValue, resolved.ContextValue),
        "unsupported SOLIDWORKS ordinary body archive version", BodyUnsupported)}
    for name, schema in [(name, 2) for name in sorted(REF_CLASSES | {THIN_FEATURE, THIN_SPEC, RADIUS_CLASS})] + [
        ("moRevCutThin_c", 1), ("moRevolvedRadiusDim_c", 1),
    ]:
        result[name] = refusal(lambda: CheckBodyMut(context, ArchiveNode(RuntimeClass(name, schema), {})),
                               "unsupported SOLIDWORKS body class", BodyUnsupported)
    return result


def worker(capture, case, edited):
    _, rows = load_lock(capture)
    raw, sha, state = input_case(capture, rows[case], edited)
    blocked = guard_runtime()
    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    typed = inspect_thin(link, state, state["profile"], edited)
    public = refusal(lambda: ReadRevOwners(link), "unqualified feature class")
    streams = audit_streams(archive, link)
    negatives = check_guards(archive, link) if case == next(iter(CASES)) and not edited else None
    require(not blocked, "typed archive unexpectedly accessed an external resource")
    return {"case": case, "edited": edited, "native_sha256": sha, "typed": typed, "streams": streams,
            "ordinary_projection": public, "schema_negatives": negatives, "runtime_external_access_attempts": 0}


def batch(capture, output):
    lock, rows = load_lock(capture)
    controls = {}
    for label in ("control-before", "control-after"):
        control = receipt(capture / (label + ".json"), lock[label]["sha256"])
        require(lock[label]["passed"] and control["sha256"] == lock["control_sha256"]
                and control["opened"] and control["rebuilt"]
                and control["open_errors"] == control["open_warnings"] == control["whats_wrong"] == 0,
                "healthy bracket control changed")
        controls[label] = lock[label]
    abi = Path(__file__).resolve()
    root = abi.parents[5]
    implementation = [f"{LAYOUTS}/{name}.py" for name in LAYOUT_NAMES] + [f"{ARCHIVE}/Resolved/MakeResolvedCtx.py"]
    tools = (abi, abi.with_name("ThinWireOwners.py"), abi.parents[1] / "EndModes" / "AuditRevEndOwners.py")
    results = []
    for name in rows:
        for state in ("original", "edited"):
            command = [sys.executable, "-B", str(abi), "--capture", str(capture), "--worker", name, state]
            response = run(command, check=True, stdout=PIPE, text=True)
            results.append(json.loads(response.stdout))
    report = {
        "schema": "kit.sw2026.thin-revolve-disclosed-archive.v1", "source_lock_sha256": SOURCE_LOCK,
        "source_revision": lock["source_revision"], "source_sdk_tree": lock["source_tree"], "oracle_build": VERSION,
        "oracle_sha256": ORACLE, "source_lifecycle": lock["sources"], "control_sha256": lock["control_sha256"],
        "control_phases": controls, "oracle_processes_in_prior_source_lock": lock["distinct_processes"],
        "fresh_host_processes": len(results), "exact_linked_streams": sum(len(r["streams"]) for r in results),
        "tool_sha256": {str(p.relative_to(root)): digest(p.read_bytes()) for p in tools},
        "implementation_sha256": {p: digest((root / p).read_bytes()) for p in implementation},
        "rows": results, "native_execution": False, "writer_output_count": 0, "heldout_acceptance": False,
    }
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    return report


def main():
    parser = ArgumentParser(description="Read and re-emit the four hash-bound disclosed thin revolve archives")
    parser.add_argument("--capture", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--report", type=Path)
    mode.add_argument("--worker", nargs=2, metavar=("CASE", "STATE"))
    args = parser.parse_args()
    if args.worker is not None:
        case, state = args.worker
        require(case in CASES and state in ("original", "edited"), "unrecognized disclosed thin case or lifecycle state")
        print(json.dumps(worker(args.capture, case, state == "edited"), ensure_ascii=False, allow_nan=False))
    else:
        result = batch(args.capture, args.report)
        print(f"{result['exact_linked_streams']} exact linked streams in {result['fresh_host_processes']} guarded reads")


if __name__ == "__main__":
    main()
