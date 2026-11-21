from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
import json
from math import isclose
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent / "serial")]

from Classes import registry
from Core import Obj
from RoundTrip import PLANS, REQUIRED, stream_roundtrip
from defs.ConfigPart import load_config, store_config_state
from defs.ResolvedCore import load_resolved, store_resolved
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

from FilletArchiveKernel import audit_kernel
from FilletArchiveOwners import CONFIG, RESOLVED, audit_owners
from FilletModel import predict, require, validate_cases
from FilletPacket import BUILD, CONTROL, ORACLE
from SealFilletSources import DISCLOSED_JOB, DISCLOSED_LOCK, REGISTRATION, validate_completed_lock

VERSION = 19000
CODEC_BASELINE = "8797d0782d9d5635e004710d462518e88c23b15e"
STREAMS = ("Header2", "Contents/CMgrHdr2", *REQUIRED)
NAMES = ("EdgeFilletAxial", "EdgeFilletTransverse")
PHASES = ("author", "reopen-edit-save", "edited-reopen")
SCHEMAS = {
    "re/data/Serialization/SerializeMap2026.json":
        "dbb788346ee44610cb365a44e6150a8264b03f93fed9832a19caa8ad24dabec4",
    "re/tooling/sw2026/serial/defs/ResolvedFillet.py":
        "b4d1e51baaa2fd6b0b864baedd191177d98193f717aa2058320bcc673ecbf0bc",
    "re/tooling/sw2026/serial/defs/ResolvedRefs.py":
        "b0ff1ee52afc7e4e528d0eab780dc8c2d359fe019fa0de4525bf8940ecdae576",
    "re/tooling/sw2026/serial/defs/ResolvedDims.py":
        "7197676232c6a07616f87384e7630ea998ef598d81bf64020d3541ff986e645a",
    "re/tooling/sw2026/serial/defs/ConfigPart.py":
        "861747fe96fde0ea8c98d3f17597177587d72e9ddfae3c185fa4d40c1caa87a9",
    "re/tooling/sw2026/serial/defs/ResolvedCore.py":
        "dbd41924f02e18da88765be32aaee9449ae145635397159c52903b30fc85761c",
    "re/tooling/sw2026/serial/RoundTrip.py":
        "c4f307e4a2b4277351ff919d0cc54ea68c76193986b417d654f38df59a5fd5ae",
}


def digest(raw):
    return sha256(raw).hexdigest()


def checked(path, expected):
    raw = path.read_bytes()
    require(digest(raw) == expected, f"wrong disclosed SHA-256 for {path.name}")
    return raw


def checked_json(path, expected):
    return json.loads(checked(path, expected))


def guard_runtime():
    blocked = []
    for encoding in ("ascii", "latin-1", "cp1252", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(encoding)

    def audit(event, _args):
        if event in ("open", "os.listdir", "os.scandir", "os.exec", "os.fork", "os.forkpty",
                     "os.system", "os.posix_spawn", "ctypes.dlopen") or event.startswith(("socket.", "subprocess.")):
            blocked.append(event)
            raise RuntimeError(f"guarded fillet archive attempted external access: {event}")

    sys.addaudithook(audit)
    return blocked


def process_id(record):
    identity = record["oracle_identity"]
    require(identity["file_version"] == BUILD and identity["sha256"] == ORACLE and identity["version_matches"]
            and identity["pe_machine"] == "0x8664", "source phase ran on a different native build")
    return identity["process_id"], identity["process_creation_filetime"]


def controls(capture, lock):
    identities = []
    for side in ("before", "after"):
        row = lock["controls"][side]
        record = checked_json(capture / f"control-{side}" / "Record.json", row["receipt_sha256"])
        require(record["passed"] and record["opened"] and record["rebuilt"] and record["sha256"] == CONTROL
                and record["open_errors"] == record["open_warnings"] == 0,
                "an immutable disclosed control did not open and rebuild cleanly")
        identities.append(process_id(record))
    return identities


def near_values(actual, expected, message):
    require(all(isclose(a, b, rel_tol=0.0, abs_tol=1e-10) for a, b in zip(actual, expected, strict=True)), message)


def observe_native(case, state, edited, constants):
    driver, definition, body = (state[key] for key in ("driver", "definition", "body"))
    props, inputs = definition["properties"], definition["inputs"]
    radius = case["edit_radius_mm" if edited else "radius_mm"] / 1000
    first, fillet_name, _ = driver["name"].split("@")
    stock_name, = definition["parents"]
    require(first == "D1" and driver["value_si"] == props["DefaultRadius"] == radius and not driver["read_only"]
            and driver["kind"] == constants["swRadialDimension"] and driver["driven_state"] == constants["swDimensionDriving"]
            and props["Type"] == constants["swConstRadiusFillet"]
            and props["ConicTypeForCrossSectionProfile"] == constants["swFeatureFilletCircular"]
            and props["selected_edge_count"] == 1 and props["multiple_radius_items_count"] == -1
            and definition["type"] == "Fillet" and all(not props[key] for key in (
                "PropagateToTangentFaces", "IsMultipleRadius", "AsymmetricFillet", "RoundCorners",
                "EnablePartialEdgeParameters", "CurvatureContinuous", "ConstantWidth")),
            "native feature does not have the independently authored editable single-edge profile")
    require(inputs["edge_reference"] and inputs["stock_boss_reference"] and len(inputs["adjacent_face_references"]) == 2
            and len(set(inputs["adjacent_face_references"])) == 2 and all(inputs["adjacent_face_references"]),
            "native rollback selection did not retain its edge and two separate stock faces")
    expected = predict(case, radius)
    for actual, target in zip(sorted(inputs["endpoints_m"]), sorted(expected["source_edge"]), strict=True):
        near_values(actual, target, "native selected edge differs from independent stock geometry")
    cylinder = body["cylinder"]["params"]
    axis = expected["edge_axis"]
    require(body["bodies"] == 1 and body["counts"] == expected["counts"] and len(cylinder) == 7
            and abs(cylinder[3 + axis]) == 1.0 and cylinder[6] == radius
            and all(cylinder[3 + index] == 0.0 for index in range(3) if index != axis),
            "native single cylindrical fillet disagrees with independent geometry")
    for index in range(3):
        if index != axis:
            near_values([cylinder[index]], [expected["fillet_axis_origin"][index]], "native fillet axis position differs")
    return {"radius_m": radius, "stock_depth_m": case["size_mm"][2] / 1000, "fillet_name": fillet_name,
            "stock_name": stock_name, "body_counts": body["counts"],
            "native_radial_dimension_name": driver["name"], "edge_endpoints_m": sorted(inputs["endpoints_m"]),
            "adjacent_stock_faces": 2, "cylinder_m": cylinder, "volume_area_centroid_si": {
                "volume": body["native"]["volume"], "area": body["native"]["area"], "centroid": body["native"]["com"]}}


def input_custody(capture):
    lock = checked_json(capture / "SourceLock.json", DISCLOSED_LOCK)
    validate_completed_lock(lock, "disclosed")
    require(lock["job_sha256"] == DISCLOSED_JOB and tuple(row["case"] for row in lock["sources"]) == NAMES
            and lock["spec_sha256"] == "d985611e397e943860b8b0ce4b3f9631e6c31f5355bdd784519a2b028a9a51cb",
            "different completed source job or case order")
    registration = checked_json(capture / "RegisteredApi.json", REGISTRATION)
    definitions = validate_cases(checked_json(HERE / "DisclosedFilletInputs.json", lock["spec_sha256"]))
    identities = controls(capture, lock)
    inputs = []
    for definition, source in zip(definitions, lock["sources"], strict=True):
        name = definition["name"]
        require(name == source["case"] and tuple(row["phase"] for row in source["phases"]) == PHASES,
                "source phase order differs")
        records = []
        for phase, row, numeric_checks in zip(PHASES, source["phases"], (31, 40, 19), strict=True):
            record = checked_json(capture / name / phase / "Record.json", row["receipt_sha256"])
            require(record["job"] == {"case": definition, "phase": phase} and record["passed"]
                    and record["source_immutable"] and record["writer_output_count"] == 0
                    and row["passed"] and row["checks"] == row["checks_passed"] == numeric_checks == len(record["checks"])
                    and all(check["passed"] for check in record["checks"])
                    and row["native_sha256"] == record["native_sha256"], "source lifecycle receipt differs")
            if phase != "author":
                require(record["open_status"] == {"opened": True, "errors": 0, "warnings": 0}
                        and record["before_explicit_rebuild"] == {"bodies": 1, "errors": 0}, "native cold open differs")
            records.append(record)
            identities.append(process_id(record))
        require(records[0]["native_sha256"] == source["original_sha256"]
                and records[1]["native_sha256"] == records[2]["native_sha256"] == source["edited_sha256"],
                "source and derivative digests do not bind to the original phases")
        inputs.append((name, source, records))
    require(len(set(identities)) == len(identities) == 8, "source lifecycle did not use eight distinct native processes")
    return lock, registration["constants"], inputs


def stream_result(archive, reg, name):
    row = stream_roundtrip(archive, name, reg, {**PLANS, **reg.plans}, linked=True)
    require(row.get("identical") and row["passed"] and row["tail"] == 0,
            f"typed stream replay failed for {name}: {row.get('error', 'mismatch')}")
    usage = row["schema_usage"]
    for detail in (usage["load"], usage["store"], *usage["dependencies"]):
        require(detail["completed"] and not detail["missing_schemas"], "reachable schema is missing")
    require(usage["load"]["provisional_schemas"] == usage["store"]["provisional_schemas"]
            == (["mo_dynSurfIdArr.Serialize"] if name == RESOLVED else []),
            "reachable provisional schema inventory changed")
    raw_fields = {}
    for direction in ("load", "store"):
        fields = usage[direction]["raw_operations"]
        require(all(item["completed"] and item["declared_length"] == item["observed_length"] == 8 for item in fields),
                "archive used an unexpected residual width")
        raw_fields[direction] = [{key: field[key] for key in ("schema", "object_class", "field", "observed_length")}
                                 for field in fields]
    def wire_fields(fields):
        return [(field["schema"], field["field"], field["observed_length"]) for field in fields]

    require(wire_fields(raw_fields["load"]) == wire_fields(raw_fields["store"]),
            "load/store residual wire inventory differs")
    return {key: row[key] for key in ("bytes", "sha256", "map_base", "map_count", "tail", "identical")} | {
        "used_schema_count": len(usage["load"]["used_schemas"]),
        "provisional_schemas": usage["load"]["provisional_schemas"], "raw_fields": raw_fields if raw_fields["load"] else {}}


def config_link(archive, reg):
    values = {"archive": archive, "name": CONFIG}
    original, config = load_config(archive.require(CONFIG), reg, VERSION, **values)
    resolved, context = load_resolved(archive.require(RESOLVED), reg, VERSION, archive=archive, name=RESOLVED,
                                      seed=config.map_state())
    rewritten, seed = store_config_state(original, reg, VERSION)
    require(rewritten == archive.require(CONFIG) and seed.count == context.base == config.count
            and not original.tail and not resolved.tail, "resolved map must inherit the whole exact configuration")
    require(store_resolved(resolved, reg, VERSION, seed=seed) == archive.require(RESOLVED),
            "resolved replay differs with the re-emitted Config-0 map")
    return original, resolved, context


def inspect(raw, reg, observed):
    archive = SldprtArchive.from_bytes(raw)
    require(ContainerMo(archive.streams) == VERSION and archive.format_version == 4,
            "unexpected 2026 archive version")
    result = {name: stream_result(archive, reg, name) for name in STREAMS}
    config, resolved, context = config_link(archive, reg)
    headers = tuple(ReadHeaderGraph(archive.require(name), VERSION) for name in ("Header2", CONFIG + "-ModelHeader"))
    atom, owned = audit_owners(config, resolved, headers, observed)
    kernel = audit_kernel(archive, atom, observed)
    try:
        ReadNativeLink(archive, 0)
    except BodyUnsupported as error:
        require(str(error) == "unsupported SOLIDWORKS body class Fillet_c schema 1", "strict boundary changed")
        refusal = str(error)
    else:
        raise ValueError("strict production reader unexpectedly accepted the research-only fillet profile")
    descriptors = {}
    for entry in context.map_state().state.EntriesValue:
        obj = entry.EntryValue
        if isinstance(obj, Obj):
            descriptors.setdefault(obj.cls, set()).add(obj.schema)
    return {"archive_version": VERSION, "container_version": archive.format_version, "streams": result,
            "resolved_materialized_classes": {name: sorted(schemas) for name, schemas in sorted(descriptors.items())},
            "strict_production_refusal": refusal, "owners": owned, "cached_partition": kernel}


def worker(capture, name, edited):
    lock = checked_json(capture / "SourceLock.json", DISCLOSED_LOCK)
    source, = (row for row in lock["sources"] if row["case"] == name)
    spec = checked_json(HERE / "DisclosedFilletInputs.json", lock["spec_sha256"])
    case, = (row for row in spec["cases"] if row["name"] == name)
    registration = checked_json(capture / "RegisteredApi.json", REGISTRATION)
    phase = source["phases"][2 if edited else 1]
    record = checked_json(capture / name / phase["phase"] / "Record.json", phase["receipt_sha256"])
    fingerprint = source["edited_sha256" if edited else "original_sha256"]
    raw = checked(capture / name / (name + ("Edited" if edited else "") + ".SLDPRT"), fingerprint)
    observed = observe_native(case, record["reopened"], edited, registration["constants"])
    reg = registry()
    blocked = guard_runtime()
    result = inspect(raw, reg, observed)
    require(not blocked, "guarded archive proof performed external data access")
    return result | {"case": name, "edited": edited, "source_sha256": fingerprint, "source_bytes": len(raw),
                     "native_reopen": observed, "phase_receipt_sha256": phase["receipt_sha256"],
                     "runtime_external_access_attempts": 0}


def supervise(capture):
    lock, _, inputs = input_custody(capture)
    for path, expected in SCHEMAS.items():
        checked(ROOT / path, expected)
    records = []
    for case, _, _ in inputs:
        for phase in ("original", "edited"):
            result = subprocess.run((sys.executable, "-B", str(Path(__file__)), "--capture", str(capture),
                                     "--worker", case, phase), check=True, capture_output=True)
            require(not result.stderr, "archive worker emitted diagnostics")
            records.append(json.loads(result.stdout))
    descriptors = records[0]["resolved_materialized_classes"]
    require(all(row.pop("resolved_materialized_classes") == descriptors for row in records),
            "disclosed object-class inventory changed")
    for original, edited in zip(records[::2], records[1::2], strict=True):
        require(original["case"] == edited["case"] and original["source_sha256"] != edited["source_sha256"]
                and original["owners"]["radial_driver"]["radius_m"] != edited["owners"]["radial_driver"]["radius_m"],
                "disclosed edit did not retain a distinct driving value")
    return {
        "schema": "kit.sw2026.edge-fillet-archive-read.v1", "oracle_build": BUILD, "oracle_sha256": ORACLE,
        "source_job_sha256": DISCLOSED_JOB, "source_lock_sha256": DISCLOSED_LOCK, "registered_api_sha256": REGISTRATION,
        "source_revision": lock["source_revision"], "codec_baseline": CODEC_BASELINE, "schema_source_sha256": SCHEMAS,
        "resolved_materialized_classes": descriptors,
        "source_phase_receipt_sha256": {
            row["case"]: {phase["phase"]: phase["receipt_sha256"] for phase in row["phases"]}
            for row in lock["sources"]},
        "bracket_receipt_sha256": {role: row["receipt_sha256"] for role, row in lock["controls"].items()},
        "passed": True, "byte_identical_archive_streams": sum(len(row["streams"]) for row in records),
        "byte_identical_active_kernel_record_sets": sum(row["cached_partition"]["active_replay"]["byte_identical"] for row in records),
        "strict_production_reads_admitted": 0, "native_source_processes_verified": 8, "native_processes_started": 0,
        "heldout_cases": 0, "writer_outputs": 0, "results": records,
    }


def main():
    parser = ArgumentParser(description="Check the four checksum-bound disclosed SOLIDWORKS 2026 fillet saves")
    parser.add_argument("--capture", type=Path, required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--report", type=Path)
    action.add_argument("--worker", nargs=2, metavar=("CASE", "PHASE"))
    args = parser.parse_args()
    if args.worker:
        case, phase = args.worker
        require(case in NAMES and phase in ("original", "edited"), "expected one exact disclosed asset")
        print(json.dumps(worker(args.capture, case, phase == "edited"), sort_keys=True, allow_nan=False))
        return 0
    require(not args.report.resolve().is_relative_to(args.capture.resolve()), "report must stay outside source custody")
    result = supervise(args.capture)
    with args.report.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({key: result[key] for key in ("passed", "byte_identical_archive_streams",
                                                   "byte_identical_active_kernel_record_sets", "writer_outputs")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
