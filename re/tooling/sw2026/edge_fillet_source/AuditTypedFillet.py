from argparse import ArgumentParser
from pathlib import Path
import json
import subprocess
import sys

from AuditFilletArchive import (
    BUILD, CONFIG, CONTROL, DISCLOSED_LOCK, HERE, NAMES, ORACLE, RESOLVED, ROOT, VERSION,
    SldprtArchive, audit_owners, checked, checked_json, digest, guard_runtime, input_custody, registry, require,
)
from Core import ArchiveMap, Obj
from ResolvedBridge import MBSM, make_node
from Streams import StreamDoc
from defs.ResolvedCore import store_resolved_state_compat

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

BASELINE_REPORT = ROOT / "re/solidworks/measurements/2026/EdgeFilletArchiveRead01.json"
BASELINE_PIN = "e7573a71c5fb709a26ae512a332f3fe6eecca5fef949b8f98380ac7cbd1337f3"
BASELINE_REVISION = "69fea01776309f9bf2d39c8be10c922672edd8f9"
DEFAULT_REFUSAL = "unsupported SOLIDWORKS body class Fillet_c schema 1"


def expect_refusal(action, message):
    try:
        action()
    except BodyUnsupported as error:
        require(str(error) == message, f"unexpected bounded fillet refusal: {error}")
        return str(error)
    raise ValueError("unsupported fillet boundary was admitted")


def change_field(record, key, value, action):
    existed, previous = key in record, record.get(key)
    record[key] = value
    try:
        return action()
    finally:
        if existed:
            record[key] = previous
        else:
            del record[key]


def shape_contrasts(doc, reg, seed, config, context):
    fillet, = (node for node in doc.roots if node.cls == "Fillet_c")

    def verify(message):
        payload, _ = store_resolved_state_compat(doc, reg, VERSION, seed=seed)
        return expect_refusal(lambda: ReadResolvedMut(payload, VERSION, config.MapValue, context, ReadFillets=True),
                              message)

    surfaces = fillet["f820"]["f18"]
    one = {"n": 1, "items": surfaces["items"][:1]}
    wrong_count = change_field(fillet["f820"], "f18", one,
                               lambda: verify("unsupported SOLIDWORKS native field path fillet keeper count"))
    wrong_mode = change_field(fillet.f, "has_f8e0", 1, lambda: change_field(
        fillet.f, "f8e0", {"n": 0, "items": []},
        lambda: verify("unsupported SOLIDWORKS native field path fillet component arrays")
    ))
    return {"single_keeper_surface": wrong_count, "alternate_component_array": wrong_mode}


def typed_file(raw, expectation, reg, run_contrasts):
    archive = SldprtArchive.from_bytes(raw)
    headers = tuple(ReadHeaderGraph(archive.require(name), VERSION) for name in ("Header2", CONFIG + "-ModelHeader"))
    config = ReadConfigMut(archive.require(CONFIG), VERSION, headers[1], NodeMaker=make_node)
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), VERSION)
    context = MakeLinkContext(config, manager)
    payload = archive.require(RESOLVED)
    resolved = ReadResolvedMut(payload, VERSION, config.MapValue, context, NodeMaker=make_node, ReadFillets=True)
    require(resolved.MapValue.CounterValue == expectation["streams"][RESOLVED]["map_count"]
            and resolved.MapBase == config.MapValue.CounterValue == expectation["streams"][RESOLVED]["map_base"],
            "typed production map differs from its actual native counterpart")
    proof = resolved.ReportValue
    require(proof["completed"] and not proof["missing_schemas"] and not proof["provisional_schemas"],
            "production body registry did not consume the complete resolved stream")
    config_data, re_emitted = WriteConfigMut(config.RootValue, VERSION, config.HeaderValue)
    require(config_data == archive.require(CONFIG), "typed inherited Config-0 does not re-emit identically")
    doc = StreamDoc("resolved", {"base": resolved.MapBase, "n": len(resolved.RootsValue), "context": context,
                                 "mbsm": Obj(MBSM, resolved.ExtraFields)}, list(resolved.RootsValue))
    seed = ArchiveMap(snapshot=re_emitted.MapValue)
    data, store_map = store_resolved_state_compat(doc, reg, VERSION, seed=seed)
    require(data == payload and store_map.count == resolved.MapValue.CounterValue,
            "unchanged research store differs when given the shared typed production graph")
    config_doc = StreamDoc("config", {}, [config.RootValue])
    _, owners = audit_owners(config_doc, doc, headers, expectation["native_reopen"])
    require(owners == expectation["owners"], "typed production ownership differs from the independent replay")
    fields = [item for item in proof["native_byte_fields"] if item.get("schema") == "dm.FUN_4bd03960"]
    require([item["object_class"] for item in fields] == ["moDisplayDistanceDim_c", "moDisplayRadialDim_c"]
            and all(item["element_type"] == "f64" and item["element_count"] == 1
                    and item["declared_length"] == item["observed_length"] == 8 and item["completed"] for item in fields)
            and [item["typed_values"][0] for item in fields]
            == [expectation["native_reopen"][key] for key in ("stock_depth_m", "radius_m")],
            "production display vectors are not independently typed binary64 values")
    refusals = {
        "default_read": expect_refusal(lambda: ReadNativeLink(archive, 0), DEFAULT_REFUSAL),
        "ordinary_store": expect_refusal(lambda: WriteResolMut(
            resolved.RootsValue, resolved.ExtraFields, VERSION, re_emitted.MapValue, context), DEFAULT_REFUSAL),
    }
    if run_contrasts:
        invalid = context | {"cmgr_f658": 0}
        refusals["alternate_archive_context"] = expect_refusal(lambda: ReadResolvedMut(
            payload, VERSION, config.MapValue, invalid, ReadFillets=True),
            "unsupported ordinary SOLIDWORKS fillet archive context")
        refusals.update(shape_contrasts(doc, reg, seed, config, context))
    return {"source_sha256": digest(raw), "config_sha256": digest(config_data), "resolved_sha256": digest(data),
            "byte_identical": True, "typed_map": [resolved.MapBase, resolved.MapValue.CounterValue],
            "native_owners_match": True, "typed_driver_values_m": {item["object_class"]: item["typed_values"][0]
            for item in fields}, "completed_schema_count": len(proof["used_schemas"]), "refusals": refusals}


def worker(capture, name, edited):
    baseline = checked_json(BASELINE_REPORT, BASELINE_PIN)
    expected, = (row for row in baseline["results"] if row["case"] == name and row["edited"] == edited)
    stem = name + ("Edited" if edited else "")
    raw = checked(capture / name / (stem + ".SLDPRT"), expected["source_sha256"])
    reg = registry()
    blocked = guard_runtime()
    row = typed_file(raw, expected, reg, name == NAMES[0] and not edited)
    require(not blocked, "fillet reader attempted external access")
    return row | {"case": name, "edited": edited, "runtime_external_access_attempts": 0}


def check_control(raw):
    blocked = guard_runtime()
    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    config, seed = WriteConfigMut(link.ConfigValue.RootValue, VERSION, link.ConfigValue.HeaderValue)
    resolved, _ = WriteResolMut(link.ResolvedValue.RootsValue, link.ResolvedValue.ExtraFields, VERSION,
                                seed.MapValue, link.ResolvedValue.ContextValue)
    require(config == archive.require(CONFIG) and resolved == archive.require(RESOLVED)
            and (link.ResolvedValue.MapBase, link.ResolvedValue.MapValue.CounterValue) == (109, 268)
            and not blocked, "ordinary typed control did not retain its prior data and map")
    return {"source_sha256": CONTROL, "config_sha256": digest(config), "resolved_sha256": digest(resolved),
            "typed_map": [109, 268], "byte_identical": True, "runtime_external_access_attempts": 0}


def launch(*args):
    process = subprocess.run((sys.executable, "-B", str(HERE / "AuditTypedFillet.py"), *args),
                             check=False, capture_output=True, text=True)
    require(process.returncode == 0 and not process.stderr, f"guarded typed fillet proof failed: {process.stderr}")
    return json.loads(process.stdout)


def main():
    parser = ArgumentParser(description="Check the opt-in typed SOLIDWORKS fillet reader on exact disclosed inputs")
    parser.add_argument("--capture", type=Path)
    parser.add_argument("--control", type=Path, required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--report", type=Path)
    action.add_argument("--control-worker", action="store_true")
    action.add_argument("--worker", nargs=2, metavar=("CASE", "PHASE"))
    args = parser.parse_args()
    if args.control_worker:
        row = check_control(checked(args.control, CONTROL))
        print(json.dumps(row, sort_keys=True, allow_nan=False))
        return 0
    require(args.capture is not None, "disclosed capture path required")
    if args.worker:
        name, phase = args.worker
        require(name in NAMES and phase in ("original", "edited"), "expected one exact disclosed file")
        print(json.dumps(worker(args.capture, name, phase == "edited"), sort_keys=True, allow_nan=False))
        return 0
    require(not args.report.resolve().is_relative_to(args.capture.resolve()), "keep output outside input custody")
    input_custody(args.capture)
    base_args = ("--control", str(args.control))
    results = [launch(*base_args, "--capture", str(args.capture), "--worker", name, phase)
               for name in NAMES for phase in ("original", "edited")]
    control = launch(*base_args, "--control-worker")
    report = {"schema": "kit.sw2026.edge-fillet-production-read.v1", "oracle_build": BUILD, "oracle_sha256": ORACLE,
              "source_lock_sha256": DISCLOSED_LOCK, "exact_disclosed_baseline_sha256": BASELINE_PIN,
              "baseline_revision": BASELINE_REVISION, "passed": True, "disclosed_typed_reads": len(results), "strict_control": control,
              "native_launches": 0, "heldout_cases_read": 0, "public_fillets_qualified": False,
              "native_writer_qualified": False, "results": results}
    with args.report.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"disclosed_typed_reads": len(results), "control_passed": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
