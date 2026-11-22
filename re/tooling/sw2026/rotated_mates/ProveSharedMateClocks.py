from argparse import ArgumentParser
from dataclasses import replace
from importlib import import_module
from json import dumps, load, loads
from pathlib import Path
from subprocess import run
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from RotatedReadAudit import ROOT, source_only
from VerifyRotatedMates import (
    NATIVE_RECORD,
    PARENT,
    RECEIPT_SHA,
    bind,
    finger,
    load_bound,
    paired_inputs,
    read_bound,
    refuse,
    require,
)


HEADERS = ("Header2", "Contents/Config-0-ModelHeader")
MATES = "Contents/Config-0-MatesList"
CLOCK_STREAMS = {*HEADERS, MATES}
CONSTRUCTORS = (
    "Assembly/RecordMateMut.py",
    "AssemblyGroups/GroupMateIn.py",
    "AssemblyGroups/MakeGroupMut.py",
    "Header/MakeRootLog.py",
)


def epochs(bundle):
    return tuple(row["created_at"] for row in bundle["mates"])


def build_case(bundle, clocks):
    from BuildHistoricalRotated import PARENT_ORDER, historical_child
    from ProjectRotatedModel import author_model, literal_recipes
    from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.MakePlanarGroup import MakePlanarGroup
    from convert.adapters.solidworks.Container.Container import BuildSldprt
    from convert.adapters.solidworks.Core.AssemblyPreparation.PlanAsmWrite import PlanAsmWrite

    model = author_model(bundle)
    output = bundle["assembly"]["output"]
    plan = PlanAsmWrite(model, output["path_name"], output["saved_at"])
    parent, child, dimensions = literal_recipes(bundle, plan)
    child = historical_child(plan.ChildDocument, child, dimensions)
    rows = tuple(replace(row, CreatedAt=tick) for row, tick in zip(plan.MatesValue, clocks, strict=True))
    assembly = MakePlanarGroup(child, parent, plan.Occurrences, rows, plan.FixedIndex)
    linked = BuildSldprt({name: assembly.StreamsValue[name] for name in PARENT_ORDER}, FormatVersion=4)
    return linked, child.BytesValue, assembly, parent, rows


def read_clock(node):
    fields = node.FieldsValue
    words = [fields[name] for name in ("f2a0", "f2a4")]
    require(all(type(value) is int and -(1 << 31) <= value < 1 << 31 for value in words),
            "mate filetime words must both be signed 32-bit")
    ticks = (words[0] & 0xFFFFFFFF) | ((words[1] & 0xFFFFFFFF) << 32)
    seconds, residue = divmod(ticks, 10_000_000)
    return seconds - 11644473600, residue, words


def read_archive(raw, bundle, times, *, fresh):
    from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadLogItems import ReadLogItems
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
    from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    mates = ReadMatesMut(archive.require(MATES), link.ResolvedValue)
    found = []
    for node, authored in zip(mates.RootsValue, bundle["mates"], strict=True):
        name = ReadNodeName(node)
        actual, residue, words = read_clock(node)
        owned = node.FieldsValue["f08"]
        require(name == authored["name"] and type(owned) is int, "mate event owner changed")
        found.append({"id": owned, "name": name, "time": actual, "subsecond_ticks": residue, "words": words})
    if fresh:
        require(tuple(row["time"] for row in found) == times
                and all(row["subsecond_ticks"] == 0 for row in found),
                "the exact whole-second mate intent changed")
    else:
        require(all(row["subsecond_ticks"] > 0 for row in found), "the native fractional clock contrast was lost")
    require(len({row["id"] for row in found}) == len(found), "mate owners collide")

    receipt = {}
    document = bundle["assembly"]["provenance"]
    for stream in HEADERS:
        fields = ReadHeaderGraph(archive.require(stream), 19000).FieldsValue
        logs = ReadLogItems(fields["f20"], "moLogs_c")
        entries = []
        for mate in found:
            row, = (row for row in logs if row.FieldsValue["f48"] == mate["id"])
            stamp, = ReadLogItems(row, "moStamp_c")
            note = stamp.FieldsValue["f20"]
            require(row.FieldsValue["f50"].TextValue == mate["name"]
                    and stamp.FieldsValue["f18"] == mate["time"],
                    "model header does not bind the actual mate's name and event")
            if fresh:
                require(note.TextValue == document["comment"]
                        and all(stamp.FieldsValue[key] == 0 for key in ("f08", "f0c", "f10")),
                        "mate header attribution changed")
            entries.append({"id": mate["id"], "time": stamp.FieldsValue["f18"]})
        if fresh:
            require((fields["f70"], fields["f50"]) == (document["created_at"], document["modified_at"]),
                    "mate creation changed a document clock")
        receipt[stream] = {"mate_stamps": entries, "document_created": fields["f70"],
                           "document_modified": fields["f50"]}
    return {"headers": receipt, "mates": found, "base": mates.MapBase}


def reject_clocks(case, clock):
    from convert.adapters.solidworks.Archive.Construction.Assembly.RecordMateMut import RecordMateMut

    _, _, assembly, input_value, rows = case
    for invalid in (-1, 1 << 32, True, 17.5):
        refuse(lambda: replace(rows[0], CreatedAt=invalid), "must fit unsigned unix seconds")
    headers = (assembly.HeaderValue, assembly.TopHeader)
    state = assembly.StateValue
    def cursors():
        return (state.CurrentConfig.FieldsValue["f85c"],
                tuple((header.FieldsValue["f08"], header.FieldsValue["f20"].FieldsValue["items"])
                      for header in headers))

    original = cursors()
    refuse(lambda: RecordMateMut(state, input_value, assembly.MateValues[0], headers, CreatedAt=clock),
           "differs from its actual feature creation time")
    require(original == cursors(), "a mismatched event altered the authored graph")
    return 5


def worker(bundle):
    bind(ROOT)
    import_module("convert")
    from BuildHistoricalRotated import build
    from MakeQueueRotated import make_bundle
    from ProjectRotatedModel import author_model
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.AssemblyPreparation.PlanAsmWrite import PlanAsmWrite
    from convert.adapters.solidworks.Core.AssemblyPreparation.PrepareAssembly import PrepareAssembly

    other = make_bundle()
    times = epochs(bundle)
    other_times = epochs(other)
    changed_time = other["assembly"]["output"]["saved_at"] - 31
    changed = (other_times[0], changed_time, other_times[2])
    legacy = {**other, "mates": other["mates"][1:]}
    default = legacy["assembly"]["provenance"]["created_at"]
    output = bundle["assembly"]["output"]
    with source_only(()) as accesses:
        current = build_case(bundle, times)
        original_model = author_model(bundle)
        old_plan = PlanAsmWrite(original_model, output["path_name"], output["saved_at"])
        (old_parent, _), (old_child, _) = build(bundle, old_plan)
        refuse(lambda: PrepareAssembly(original_model, output["path_name"], output["saved_at"], PublicProfile=True),
               "the rotated three-mate profile requires separate native writer qualification")
        first = build_case(other, other_times)
        contrast = build_case(other, changed)
        omitted = build_case(legacy, (None, None))
        explicit = build_case(legacy, (default, default))
        refusals = reject_clocks(current, times[1])
    require(not accesses, "construction read a data file")
    require(current[:2] == (old_parent, old_child), "shared assembly changed the historical container pair")
    require(omitted[:2] == explicit[:2] and omitted[2].BytesValue == explicit[2].BytesValue,
            "the existing two-mate default is not the document creation clock")
    require(first[1] == contrast[1], "mate creation changed the shared child")
    observed, alternate = (SldprtArchive.from_bytes(row[0]).streams for row in (first, contrast))
    require(observed.keys() == alternate.keys(), "the event changed stream topology")
    altered = {name for name in observed if observed[name] != alternate[name]}
    require(altered == CLOCK_STREAMS, "the event changed other logical streams")
    exact = read_archive(current[0], bundle, times, fresh=True)
    independent = read_archive(first[0], other, other_times, fresh=True)
    independent_changed = read_archive(contrast[0], other, changed, fresh=True)
    two_mates = read_archive(omitted[0], legacy, (default, default), fresh=True)
    require(independent["mates"][::2] == independent_changed["mates"][::2]
            and independent["mates"][1]["id"] == independent_changed["mates"][1]["id"],
            "another mate owner changed")
    return {"construction_data_reads": len(accesses), "refusals": refusals,
            "fixture": {"parent": finger(current[0]), "child": finger(current[1]), "events": exact,
                        "current_unqualified_parent": finger(current[2].BytesValue),
                        "additional_current_streams": sorted(set(current[2].StreamsValue) - SldprtArchive.from_bytes(current[0]).streams.keys())},
            "public_admission_refused": True,
            "changed_streams": sorted(altered), "independent": independent,
            "independent_changed": independent_changed, "omitted_clock_default": two_mates}


def supervise(packet, output):
    receipt = load_bound(ROOT / NATIVE_RECORD, RECEIPT_SHA)
    request, pins = paired_inputs(packet, receipt)
    bundle = request["bundle"]
    bind(ROOT)
    native = read_bound(packet / "Native/A22CombinedRotated/author" / PARENT,
                        receipt["source"]["native_parent_sha256"])
    native_events = read_archive(native, bundle, None, fresh=False)
    reports = []
    for _ in range(2):
        execution = run([sys.executable, "-I", "-B", str(HERE), "--worker"], input=dumps(bundle),
                        text=True, capture_output=True, check=False, timeout=90)
        require(execution.returncode == 0 and not execution.stderr, execution.stderr)
        reports.append(loads(execution.stdout))
    first, second = reports
    require(first == second, "different results from independent guarded workers")
    for member, pin in (("parent", "assembly"), ("child", "child")):
        exact = {key: pins[pin][key] for key in ("bytes", "sha256")}
        require(first["fixture"][member] == exact, "shared generation differs from the native-tested " + member)
    constructors = ROOT / "src/convert/adapters/solidworks/Archive/Construction"
    result = {**first, "schema": "kit.sw2026.shared-mate-creation-events.v1", "fresh_workers": 2,
              "source_and_candidate_native_receipt": RECEIPT_SHA, "native_source_events": native_events,
              "constructor_sha256": {path: finger((constructors / path).read_bytes())["sha256"] for path in CONSTRUCTORS},
              "task_method_sha256": finger(HERE.read_bytes())["sha256"],
              "reused_tool_sha256": {name: finger(HERE.with_name(name).read_bytes())["sha256"]
                                     for name in ("BuildHistoricalRotated.py", "ProjectRotatedModel.py", "MakeQueueRotated.py",
                                                  "RotatedReadAudit.py", "VerifyRotatedMates.py")}, "native_launches": 0,
              "heldout_reads": 0, "public_writer_promoted": False}
    with output.open("x", encoding="utf-8") as stream:
        stream.write(dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(finger(output.read_bytes())["sha256"])


if __name__ == "__main__":
    if sys.argv[1:] == ["--worker"]:
        print(dumps(worker(load(sys.stdin)), sort_keys=True, allow_nan=False))
    else:
        parser = ArgumentParser()
        parser.add_argument("--disclosed", required=True, type=Path)
        parser.add_argument("--output", required=True, type=Path)
        arguments = parser.parse_args()
        supervise(arguments.disclosed, arguments.output)
