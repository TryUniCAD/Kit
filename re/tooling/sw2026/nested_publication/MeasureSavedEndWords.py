from argparse import ArgumentParser
from importlib.metadata import version
from platform import python_version
from pathlib import Path
from struct import unpack_from
from subprocess import run
import json
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

import MeasureWarmNestedLeaf as warm
from TraceSavedEndWords import trace_native

from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


ROOT = warm.ROOT
PRIOR = "3250fcec388cb0edb2f408b6a2b7cf23f6e91690"
MEASURES = ROOT / "re/solidworks/measurements/2026"
WARM_PIN = "350155bb14aa5db60ae2910837b5affbdda51186a86e932b0d96bdbb477a1ae4"
ALTERNATE_PIN = "cee8f7ddad586f8b8d632f7eb2956cf81691fd399df09979f3eb9d25f045783b"
PREPARATION_PIN = "0e7b04caf1ee567c33e852bc0ccea0a2560998305d26fd1bc28f729f0277de32"
MULTISTOCK_PIN = "c62c3bd6604a3916729ed474eade455906d790955ed86135e092a2b9a78f82f0"
LADDER_MANIFEST = "re/solidworks/v2026/corpus/ladder/Manifest.json"
LADDER_PIN = "7c84fd4ef75ecf5f8b0cf00fbc12e932aa7e7955ecb5bb414c22d309f9362e79"
WORDS = ("f148", "f14c", "f150", "f154", "f158")
ALTERNATES = {
    "D01Forward.SLDPRT": ("blind", False),
    "D04Reverse.SLDPRT": ("blind", True),
    "D07MidPlane.SLDPRT": ("mid_plane", False),
    "D10TwoDirections.SLDPRT": ("two_lengths", False),
}
READ_ATOM_FIELDS = ("f28", "f544", "has_f528", "has_f530", "has_f548", "has_f3d0")


def authority(path, pin):
    return json.loads(warm.pinned(path, pin))


def bound_tool(path, pin=None):
    current = warm.digest(warm.git("show", f"{PRIOR}:{path}"))
    warm.pinned(ROOT / path, current if pin is None else pin)
    warm.require(pin is None or pin == current, "prior packet tool identity differs from this checkout")
    return current


def cold_save(workspace, references):
    sdk, = (row for row in references[warm.SDK_CONTROL]["cases"] if row["case"] == "SdkNestedNeutralNative03")
    root = workspace / "SdkNestedNeutralNative03"
    result = authority(root / "Inspection/Result.json", sdk["result_sha256"])
    warm.require(result["passed"] and result["controls_healthy"] and result["frozen_inputs_unchanged"]
                 and result["oracle_sha256"] == warm.ORACLE and result["fixture_sha256"] == sdk["fixture_sha256"]
                 and not result["heldout_inputs_read"] and result["synchronized_derivative_files_match"],
                 "cold and ended control did not pass the earlier disclosed native lifecycle")
    written, = (phase for phase in result["phases"] if phase["mode"] == "generated")
    reopened, = (phase for phase in result["phases"] if phase["mode"] == "reopen")
    saved = written["saved_files"]["plate"]
    checks = (written, reopened)
    warm.require(all(row["passed"] and row["open_errors"] == row["open_warnings"] == 0 for row in checks)
                 and saved["status"] == [True, 0, 0]
                 and reopened["initial"]["definitions"]["plate"]["sha256"]
                 == reopened["rebuilt"]["definitions"]["plate"]["sha256"] == saved["sha256"],
                 "generated and independently reopened native control file differ")
    return {
        "mode": "generated_native_save", "file": str(root / "GeneratedInput/SdkNestedPlate.SLDPRT"),
        "sha256": saved["sha256"], "bytes": saved["bytes"], "native_result_sha256": sdk["result_sha256"],
        "depth_m": sdk["driving_depth_reopened_m"],
    }


def alt_cases(workspace):
    report = authority(MEASURES / "EndSourceProcessesA651.json", ALTERNATE_PIN)
    prior = authority(MEASURES / "EndConditionPreparation02.json", PREPARATION_PIN)
    folder = workspace / "EndConditionPrepared02"
    manifest = authority(folder / "Manifest.json", prior["manifest_sha256"])
    warm.require(report["all_field_predictions_passed"] and not report["heldout_native_payloads_read"]
                 and not prior["heldout_native_payloads_read"] and not manifest["heldout_native_payloads_read"]
                 and report["file_count"] == prior["file_count"] == 14,
                 "alternate inputs lack the disclosed preparation boundary")
    manifest_records = manifest["records"]
    for row in report["report_projection"]["files"]:
        file = row["file"]
        if file not in ALTERNATES:
            continue
        item, = (entry for entry in manifest_records if entry["file"] == file)
        warm.require(row["passed"] and row["source_immutable"] and row["specification"]["split"] == "discovery"
                     and row["sha256"] == item["sha256"] and row["source_sha256"] == item["source_sha256"],
                     "alternate control differs from the known prepared discovery source")
        condition, reversed_value = ALTERNATES[file]
        observation = row["native_definition"]
        secondary = observation["reverse_depth"] if observation["both_directions"] else None
        yield {
            "mode": "alternate_end", "file": str(folder / file), "sha256": row["sha256"],
            "native_source_sha256": row["source_sha256"], "end_values": row["observed_end_spec"]["scalars"],
            "expected_semantics": [condition, observation["depth"], reversed_value, secondary],
        }


def stored_owner(archive, link, owner):
    feature = owner.NodeValue
    node = owner.EndValue
    span = warm.NativeNodeSpan(link, node)
    warm.require(feature.FieldsValue["f818"] is node and node.ClassValue == RuntimeClass("moEndSpec_c", 1)
                 and span["stream"] == link.StreamName
                 and any(entry.EntryValue is node for entry in link.ResolvedValue.MapValue.EntriesValue),
                 "end scalar interval has a detached graph or wrong schema owner")
    raw = archive.require(span["stream"])
    stop = span["end"]
    start = stop - 20
    warm.require(span["offset"] <= start < stop <= len(raw), "end field interval is not in the typed body")
    fields = node.FieldsValue
    values = {name: fields[name] for name in WORDS}
    warm.require(tuple(values.values()) == unpack_from("<iiiii", raw, start), "physical end tail differs from typed fields")
    for name in ("f28", "f48"):
        if fields["has_" + name]:
            warm.require(fields[name] == {"n": 0, "items": []}, "an alternate surface reference appears in this scope")
    marks = feature.FieldsValue.get("f3d0")
    context = link.ConfigValue.RootValue.FieldsValue.get("fe38")
    return {
        "feature_id": warm.NativeNodeId(feature), "feature_class": feature.ClassValue.NameValue,
        "profile_id": warm.NativeNodeId(owner.ProfileValue), "plain_sketch_start": fields["f140"].FieldsValue == {"t": 0},
        "logical_stream_sha256": warm.digest(raw), "end_node": span, "end_tail_interval": [start, stop],
        "saved_words": values, "solid_merge": fields["f128"],
        "surface_array_presence": [fields["has_f28"], fields["has_f48"]],
        "scope_and_archival_owners": {name: feature.FieldsValue[name] for name in READ_ATOM_FIELDS},
        "rollback_owner_ids": [marks.FieldsValue["f18"] if marks is not None else None,
                               context.FieldsValue["f18"] if context is not None else None],
        "neutral_end_semantics": [owner.ModeValue.value,
                                  owner.DepthValue.DepthValue.native_value if owner.DepthValue is not None else None,
                                  owner.IsReversed,
                                  owner.SecondValue.DepthValue.native_value if owner.SecondValue is not None else None],
    }


def inspect(job):
    path = Path(job["file"])
    warm.primed()
    guard = warm.FrozenReads({path})
    sys.addaudithook(guard.inspect)
    try:
        data = warm.pinned(path, job["sha256"], job.get("bytes"))
        document = warm.open_document(path)
        archive = warm.SldprtArchive.from_bytes(data)
        link = warm.ReadNativeLink(archive, 0)
        features = warm.IndexFeatures(link)
        if job["mode"] == "selected":
            lineage = warm.ReadTwoStockCut(link)
            typed = [*lineage.StockValues, lineage.CutValue]
            warm.require(lineage.WrapperValue.ClassValue.NameValue == "moCompSolidBody_c",
                         "multistock contrast does not have its actual selected input")
            lineage_ids = [atom.FieldsValue["f140"] for atom in (lineage.AtomsValue.ConsumedAtom,
                                                                lineage.AtomsValue.UntouchedAtom,
                                                                lineage.AtomsValue.ResultAtom)]
            warm.require(lineage_ids == [101, 102, 103], "multistock contrast changed its actual atom roles")
        else:
            sole, = (row for row in features.values() if row.ClassValue.NameValue == "moExtrusion_c")
            warm.CheckSingleBoss(features, "moExtrusion_c")
            typed = [warm.ReadExtrude(link, sole, features)]
            lineage_ids = None
        owners = [stored_owner(archive, link, owner) for owner in typed]
        partition = warm.PARTITION in archive.streams
        marks = None
        if partition and job["mode"] != "selected":
            _, _, marks = warm.ReadBodyKernel(archive.require(warm.PARTITION), warm.PARTITION)
            warm.CheckThinMarks(link.ConfigValue.RootValue, typed[0].NodeValue, marks)
        payload = {
            "mode": job["mode"], "file": path.name, "sha256": job["sha256"],
            "body_count": len(document.bodies), "partition_present": partition, "partition_marks": marks,
            "actual_stock_input_untouched_output_ids": lineage_ids, "owners": owners,
            "file_reads": sorted(guard.reads), "denied_operations": list(guard.denied),
            **{key: job[key] for key in ("author_record_sha256", "native_result_sha256", "native_source_sha256")
               if key in job},
        }
        if job["mode"] == "source":
            display = warm.observe(data)
            payload["owned_height_display"] = {key: display["height"][key]
                                               for key in ("text_m", "centerline_route", "driver")}
        warm.require(not guard.denied and guard.reads == {path.name}, "process boundary escaped the declared source")
    finally:
        guard.active = False
    warm.pinned(path, job["sha256"], job.get("bytes"))
    return payload


def invoke(job):
    proc = run((sys.executable, "-I", "-B", str(HERE), "--case"), input=json.dumps(job),
               capture_output=True, text=True, timeout=90)
    warm.require(proc.returncode == 0 and not proc.stderr,
                 f"{job['mode']} {Path(job['file']).name}: {proc.stderr[-2400:]}")
    return json.loads(proc.stdout)


def check_results(cases, originals, reference):
    finding = {name: result["owners"][0] for name, result in cases.items() if name != "selected"}
    seed = finding["ladder"]
    warm.require(seed["scope_and_archival_owners"]["f544"] == 1 and seed["rollback_owner_ids"] == [7, 3],
                 "the redacted seed no longer retains its source scope and marks")
    for row in originals:
        name = row["name"]
        actual = finding[name]
        source_record, = (record for record in reference["cases"] if record["file"] == name + ".SLDPRT")
        prior = source_record["record"]
        display = cases[name]["owned_height_display"]
        warm.require(cases[name]["sha256"] == source_record["file_sha256"]
                     and actual["saved_words"] == seed["saved_words"]
                     and actual["saved_words"]["f150"] != 0 and actual["saved_words"]["f154"] != 0
                     and actual["plain_sketch_start"] and actual["solid_merge"] == 1
                     and actual["feature_id"] == prior["creator_id"]
                     and actual["profile_id"] == prior["profile_id"]
                     and actual["rollback_owner_ids"] == prior["saved_owners"]["active_and_previous_marks"]
                     and actual["scope_and_archival_owners"] == {
                         "f28": 0xC0000140, "f544": 1, "has_f528": 1, "has_f530": 0,
                         "has_f548": 0, "has_f3d0": 1,
                     }
                     and display["text_m"] == prior["dimension_display"]["height"]["text_m"]
                     and display["centerline_route"] is True and display["driver"] == "D2"
                     and source_record["construction"]["spatial_label_differences"] == []
                     and source_record["construction"]["runtime_reads"] == 0,
                     "the exact saved source has a different owner, display, or creator than the proven profile")
    common = (
        ("cold", 0x40000140, [0, 0], None),
        ("generated_native_save", 0xC0000140, [1, 1], [16, 2]),
    )
    for name, flags, arrays, marks in common:
        actual = finding[name]
        warm.require(set(actual["saved_words"].values()) == {0}
                     and actual["scope_and_archival_owners"]["f544"] == 0
                     and actual["scope_and_archival_owners"]["f28"] == flags
                     and actual["surface_array_presence"] == arrays and cases[name]["partition_marks"] == marks,
                     "original SDK and native-resaved control no longer contrast the same options")
    selected = cases["selected"]["owners"]
    warm.require([(row["feature_id"], row["scope_and_archival_owners"]["f544"], row["solid_merge"])
                  for row in selected] == [(32, 0, 0), (40, 0, 0), (47, 1, 1)]
                 and selected[-1]["neutral_end_semantics"] == ["through_all", None, True, None]
                 and not any(selected[-1]["saved_words"][key] for key in ("f150", "f154")),
                 "selected scope and surface options no longer provide an independent contrast")


def supervise(workspace, modules):
    warm.require(warm.git("rev-parse", "HEAD:src").decode().strip() == warm.SOURCE_TREE
                 and not warm.git("status", "--porcelain", "--", "src"),
                 "this evidence requires the pinned clean production source tree")
    warm_result = authority(MEASURES / "SdkWarmNestedLeaf01.json", WARM_PIN)
    references = {name: authority(MEASURES / name, pin) for name, pin in warm.PINS.items()}
    names = ("AuthorNestedAssemblySources.py", "NestedAssemblySourcePlan.py")
    old_tools = {f"re/tooling/sw2026/{name}": bound_tool(f"re/tooling/sw2026/{name}",
                                                       references[warm.NATIVE]["tool_sha256"][name])
                 for name in names}
    for name in (HERE.with_name("MeasureWarmNestedLeaf.py"), HERE.with_name("WarmLeafBoundary.py")):
        old_tools[str(name.relative_to(ROOT))] = bound_tool(str(name.relative_to(ROOT)), warm_result["tool_sha256"][name.name])
    ladder = authority(ROOT / LADDER_MANIFEST, LADDER_PIN)
    source, = (entry for entry in ladder["records"] if entry["name"] == "L1_boss.SLDPRT")
    bound_seed = "c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57"
    plan = warm.git("show", f"{PRIOR}:re/tooling/sw2026/NestedAssemblySourcePlan.py")
    pin_statement = f'CONTROL_SHA = "{bound_seed}"'.encode()
    warm.require(source["source_sha256"] == bound_seed and pin_statement in plan.splitlines(),
                 "tracked control is not the frozen author's common seed")
    multistock = authority(MEASURES / "ThroughAllMultiStockCache01.json", MULTISTOCK_PIN)
    originals = tuple(warm.models(workspace, references))
    controls = tuple(warm.controls(workspace, references))
    warm.require(all(row["sha256"] == (source["sha256"] if row["mode"] == "ladder"
                                     else multistock["source_sha256"]["ThroughMultiStock03"])
                     for row in controls if row["mode"] != "cold"), "declared contrasts lost their provenance pins")
    native = trace_native(modules)
    alt = tuple(alt_cases(workspace))
    warm.require(len(alt) == len(ALTERNATES), "not all exact alternate discovery modes were selected")
    saved = cold_save(workspace, references)
    jobs = (*originals, *controls, saved, *alt)
    cases = {job.get("name", Path(job["file"]).stem if job["mode"] == "alternate_end" else job["mode"]): invoke(job)
             for job in jobs}
    warm.require(len(cases) == len(jobs)
                 and cases[saved["mode"]]["owners"][0]["neutral_end_semantics"][1] == saved["depth_m"],
                 "fresh-process names collapsed or the native saved depth does not match its source receipt")
    check_results(cases, originals, warm_result)
    for job in alt:
        row = cases[Path(job["file"]).stem]["owners"][0]
        warm.require(row["neutral_end_semantics"] == job["expected_semantics"]
                     and row["saved_words"] == {key: job["end_values"][key] for key in WORDS},
                     "alternate termination no longer matches its independent intact native field record")
    return {
        "schema": "kit.sw2026.warm-saved-end-words.v1", "reader_revision": warm.BASIS, "source_tree": warm.SOURCE_TREE,
        "prior_receipts_sha256": {**warm.PINS, "SdkWarmNestedLeaf01.json": WARM_PIN,
                                  "EndSourceProcessesA651.json": ALTERNATE_PIN, "EndConditionPreparation02.json": PREPARATION_PIN,
                                  "ThroughAllMultiStockCache01.json": MULTISTOCK_PIN, LADDER_MANIFEST: LADDER_PIN},
        "tool_sha256": {file.name: warm.digest(file.read_bytes())
                        for file in (HERE, HERE.with_name("TraceSavedEndWords.py"))},
        "prior_tool_sha256": old_tools, "native_static": native, "cases": cases,
        "tool_runtime": {"python": python_version(), "pefile": version("pefile"), "capstone": version("capstone")},
        "common_original_seed_sha256": bound_seed, "guarded_fresh_source_readers": len(jobs),
        "files_unchanged": True, "native_processes_started": 0, "heldout_inputs_opened": 0,
        "generated_outputs": 0, "complete_original_source_transfer": False,
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("--disclosed", type=Path)
    parser.add_argument("--modules", type=Path)
    parser.add_argument("--case", action="store_true")
    args = parser.parse_args()
    if args.case:
        result = inspect(json.load(sys.stdin))
    else:
        warm.require(args.disclosed is not None and args.disclosed.is_absolute()
                     and args.modules is not None and args.modules.is_absolute(),
                     "pass absolute disclosed input and licensed PE roots")
        result = supervise(args.disclosed, args.modules)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
