from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
import json
from pathlib import Path
from subprocess import run
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent), str(HERE)]

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from SweepArchiveLayout import SIDE, SWEEP, observe
from SweepArchiveOwners import read_owners
from SweepModel import dimensions, require, validate_spec

SOURCE_LOCK = "563aef5da24478ab83b881092561dd09066ad9b8e3999ca1da106e00e22420ca"
API = "07909437b4c7068ec0ddbb0025d6f6990d6c4bb65767bc778cddfc3577cfdffe"
JOB = "e7a321d410d278b255fe4fe220d6ef5e2e35628b416646cc454bc5cf9b14f421"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
BUILD = "34.5.2.0604"
SOURCE_REVISION = "038a8fc7aaf0ad3ba8541c325a23ef70646e9ba6"
CODEC_BASELINE = "5ed14c72bbd78f93caab1a94a3f0ca92d6979e88"
SDK_TREE = "392993e1c5f530d854c132482b268d1554d8c5c7"
SERIALIZE_MAP = "dbb788346ee44610cb365a44e6150a8264b03f93fed9832a19caa8ad24dabec4"
MODEL_BINARY = "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e"
CONFIG = "Contents/Config-0"
RESOLVED = CONFIG + "-ResolvedFeatures"
STREAMS = (CONFIG + "-ModelHeader", CONFIG, "Contents/CMgr", RESOLVED)
PHASES = ("author", "section-edit", "section-reopen", "path-edit", "path-reopen")
ROLES = ("original", "section", "path")


def digest(data):
    return sha256(data).hexdigest()


def checked(path, expected):
    require(path.is_file() and not path.is_symlink(), f"disclosed input is not a regular file: {path.name}")
    data = path.read_bytes()
    require(digest(data) == expected, f"disclosed SHA-256 changed: {path.name}")
    return data


def native_phase(capture, phases, lock, slot, case, name, role, incoming):
    proof = phases[name]
    raw = checked(capture / f"Slot{slot + 1:02d}-{name}.json", proof["receipt_sha256"])
    record = json.loads(raw)
    identity = record["oracle_identity"]
    require(identity["file_version"] == BUILD and identity["sha256"] == ORACLE
            and identity["version_matches"] and identity["pe_machine"] == "0x8664",
            "native phase does not belong to the exact oracle build")
    require(proof["passed"] and proof["job_sha256"] == JOB and proof["slot"] == slot
            and proof["worker_exit_code"] == 0 and not proof["timed_out"]
            and proof["source_sha256"] == incoming and proof["artifact_sha256"] == lock["artifact_sha256"][role]
            and record["native_sha256"] == proof["artifact_sha256"]
            and record["native_bytes"] == proof["artifact_bytes"]
            and record["job"] == {"case": case, "phase": name}
            and proof["checks"] == proof["checks_passed"] == len(record["checks"])
            and all(row["passed"] for row in record["checks"]),
            "native phase does not match its locked lifecycle or exact artifact")
    require(record["passed"] and record["source_immutable"] and record["writer_output_count"] == 0
            and record["first_failure"] is None
            and not (record["dialogs"] or record["cleanup_errors"] or record["controller_diagnostics"])
            and record["com_type_library"]["major"] == 34 and record["com_type_library"]["minor"] == 0,
            "native phase did not verify clean source custody")
    require(record.get("open_status") == (None if name == "author" else
            {"opened": True, "errors": 0, "warnings": 0})
            and record.get("native_save_status") == (None if name.endswith("reopen") else [True, 0, 0]),
            "native phase has different open or save status")
    rollback = record["last_rollback_definition"]
    require(rollback["parents"] == ["Front Plane", "Right Plane", "SweepPath", "SweepSection"]
            and rollback["profile_type"] == rollback["path_type"] == 9 and rollback["sweep_type"] == 17
            and rollback["is_boss"] and not rollback["is_thin"] and rollback["guides"] == 0
            and rollback["Direction"] == -1 and rollback["FeatureScope"] and rollback["Merge"],
            "native phase does not identify the qualified Standard sweep inputs")
    section, = record["last_SweepSection_dimensions"]
    path, = record["last_SweepPath_dimensions"]
    expected_section, expected_path = dimensions(case, None if role == "original" else role)
    require(section["value_m"] == 2 * expected_section and path["value_m"] == expected_path,
            "saved native driver differs from independently authored case")
    return {
        "proof": {"phase": name, "sha256": proof["receipt_sha256"], "checks": proof["checks_passed"]},
        "process": (identity["process_id"], identity["process_creation_filetime"]),
        "section": section,
        "path": path,
    }


def load_disclosed(capture):
    lock = json.loads(checked(capture / "SourceLock.json", SOURCE_LOCK))
    api = json.loads(checked(capture / "RegisteredApi.json", API))
    require(lock["cohort"] == "disclosed" and lock["source_revision"] == SOURCE_REVISION
            and lock["job_sha256"] == JOB and lock["api_sha256"] == API
            and lock["oracle_build"] == BUILD and lock["oracle_sha256"] == ORACLE
            and lock["fresh_processes"] == lock["distinct_processes"] == 12 and lock["passed"]
            and lock["idle_after"] and lock["inputs_unchanged"] and lock["writer_output_count"] == 0
            and lock["heldout_writer_acceptance"] is False, "wrong disclosed source lock")
    for role, row in lock["controls"].items():
        require(row["phase"] == f"control-{role}" and row["passed"] and not row["timed_out"]
                and row["job_sha256"] == JOB and row["worker_exit_code"] == 0, "native control failed")
    require(set(lock["controls"]) == {"before", "after"}
            and api["constants"]["swConstraintType_DIAMETER"] == 15
            and api["constants"]["swConstraintType_RADIUS"] == 3, "wrong native control or registered API")
    _, cases = validate_spec(json.loads(checked(HERE / "DisclosedSweepInputs.json", lock["spec_sha256"])))
    inputs = []
    processes = set()
    native_lifecycles = []
    for case, source in zip(cases, lock["sources"], strict=True):
        slot = source["slot"]
        phases = {phase["phase"]: phase for phase in source["phases"]}
        require(slot == len(inputs) // 3 and tuple(phases) == PHASES and source["passed"]
                and set(source["artifact_sha256"]) == set(ROLES), "unexpected disclosed case sequence")
        original = source["artifact_sha256"]["original"]
        records = {"author": native_phase(capture, phases, source, slot, case, "author", "original", None)}
        for role in ("section", "path"):
            edit, reopen = f"{role}-edit", f"{role}-reopen"
            records[edit] = native_phase(capture, phases, source, slot, case, edit, role, original)
            records[reopen] = native_phase(
                capture, phases, source, slot, case, reopen, role, source["artifact_sha256"][role])
            require(all(records[edit][name]["value_m"] == records[reopen][name]["value_m"]
                        for name in ("section", "path")), "edited native save changed its driver values on reopen")
        processes.update(record["process"] for record in records.values())
        native_lifecycles.append({"slot": slot + 1, "phases": [records[name]["proof"] for name in PHASES]})
        for role in ROLES:
            label = case["name"] + ("" if role == "original" else role.title() + "Edit")
            record = records["author" if role == "original" else f"{role}-reopen"]
            raw = checked(capture / f"{label}.SLDPRT", source["artifact_sha256"][role])
            inputs.append((slot, role, raw, record))
    require(len(inputs) == 6 and len(processes) == 10, "disclosed cases do not have distinct source process custody")
    return inputs, lock, native_lifecycles


def guard_runtime():
    for encoding in ("ascii", "latin-1", "cp1252", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(encoding)
    blocked = []

    def audit(event, _args):
        if event in ("open", "os.listdir", "os.scandir", "os.exec", "os.fork", "os.forkpty",
                     "os.system", "os.posix_spawn", "ctypes.dlopen") or event.startswith(("socket.", "subprocess.")):
            blocked.append(event)
            raise RuntimeError(f"sweep archive attempted external access: {event}")

    sys.addaudithook(audit)
    return blocked


def refusal(archive, mode, expected):
    with observe(mode) as observed:
        try:
            ReadNativeLink(archive, 0)
        except BodyUnsupported as error:
            (event,) = observed["refusals"]
            require(str(error) == f"unsupported SOLIDWORKS body class {expected} schema 1"
                    and event["class"] == expected and event["cursor"] == event["body_offset"],
                    "first unsupported sweep owner differs")
            return event
    raise ValueError("sweep was unexpectedly admitted by the restricted class registry")


def inspect(slot, role, raw, phases):
    archive = SldprtArchive.from_bytes(raw)
    require(archive.format_version == 4 and ContainerMo(archive.streams) == 19000, "wrong native part profile")
    baseline = refusal(archive, "baseline", SWEEP)
    intermediate = refusal(archive, "base", SIDE)
    with observe("linked") as observed:
        linked = ReadNativeLink(archive, 0)
        owners = read_owners(linked, phases)
    require(not observed["refusals"], "sweep graph retained a refused owner")
    for graph in (linked.ConfigValue, linked.ResolvedValue):
        require(graph.ReportValue["completed"] and not graph.ReportValue["missing_schemas"],
                "linked archive left an unfinished typed graph")
    return {
        "slot": slot + 1, "role": role, "file_sha256": digest(raw), "native_phase": phases["proof"],
        "baseline_refusal": baseline, "base_only_refusal": intermediate,
        "streams": {name: {"bytes": len(archive.require(name)), "sha256": digest(archive.require(name))}
                    for name in STREAMS},
        "inline_spans": observed["spans"],
        "config_next_slot": linked.ConfigValue.MapValue.CounterValue,
        "resolved_next_slot": linked.ResolvedValue.MapValue.CounterValue,
        "owners": owners,
    }


def compare(states):
    for slot in (1, 2):
        original, changed_section, changed_path = [row["owners"] for row in states if row["slot"] == slot]
        require(original["section"]["driver"]["metres"] == changed_path["section"]["driver"]["metres"]
                and original["path"]["driver"]["metres"] == changed_section["path"]["driver"]["metres"]
                and original["section"]["driver"]["metres"] != changed_section["section"]["driver"]["metres"]
                and original["path"]["driver"]["metres"] != changed_path["path"]["driver"]["metres"],
                "independent sweep edits did not retain the other driver")
        require(original["section"]["embedded_body"]["transmit_sha256"] ==
                changed_path["section"]["embedded_body"]["transmit_sha256"] !=
                changed_section["section"]["embedded_body"]["transmit_sha256"],
                "embedded section did not track only the matching section edit")


def check_sdk():
    git = ("git", "-C", str(ROOT))
    def output(*args):
        return run((*git, *args), check=True, capture_output=True, text=True).stdout.strip()
    require(output("rev-parse", CODEC_BASELINE + ":src") == SDK_TREE,
            "baseline SDK tree does not match its pinned object")
    require(not output("diff", "--name-only", CODEC_BASELINE, "--", "src")
            and not output("ls-files", "--others", "--exclude-standard", "--", "src"),
            "run the archive proof against its unchanged pinned SDK source")


def main():
    parser = ArgumentParser()
    parser.add_argument("--disclosed", type=Path, required=True)
    args = parser.parse_args()
    check_sdk()
    cases, lock, native_lifecycles = load_disclosed(args.disclosed)
    checked(ROOT / "re/data/Serialization/SerializeMap2026.json", SERIALIZE_MAP)
    tools = {name: digest((HERE / name).read_bytes()) for name in
             ("AuditSweepArchive.py", "SweepArchiveLayout.py", "SweepArchiveOwners.py")}
    blocked = guard_runtime()
    result = [inspect(*case) for case in cases]
    compare(result)
    require(not blocked, "archive observation attempted external access after custody")
    print(json.dumps({
        "schema": "kit.sw2026.standard-sweep-archive-observation.v1",
        "oracle_build": BUILD, "oracle_sha256": ORACLE, "source_lock_sha256": SOURCE_LOCK,
        "source_revision": SOURCE_REVISION, "source_tree": lock["source_tree"], "registered_api_sha256": API,
        "disclosed_job_sha256": JOB, "native_fresh_processes": lock["fresh_processes"],
        "native_controls": {name: row["receipt_sha256"] for name, row in lock["controls"].items()},
        "codec_baseline": CODEC_BASELINE, "sdk_tree": SDK_TREE, "tool_sha256": tools,
        "native_lifecycles": native_lifecycles,
        "model_binary_sha256": MODEL_BINARY, "serialize_map_sha256": SERIALIZE_MAP,
        "blocked_runtime_calls": len(blocked), "native_processes_started": 0, "private_sources_accessed": 0,
        "resolved_graph_reads": len(result), "resolved_byte_replays": 0, "writer_outputs": 0,
        "cases": result,
    }, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
