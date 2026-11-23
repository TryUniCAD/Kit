from argparse import ArgumentParser
from dataclasses import asdict, replace
import json
from pathlib import Path, PureWindowsPath
import subprocess
import sys


HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from ProveD01ConcentricBridge import AUTHOR, FILES, LOCK, REPO, VISUAL, fingerprint, model_request, proof_guard
from ProveD01ParentDisplay import build_arguments
from ProveD01RadialLabel import owned_label
from ProveD01ChildAppearance import EPOCH, wire
from ProveConcentricSourceBrep import D01_LOCKED, checked, json_digest, source_case
from ProjectD01Concentric import project_d01, require
from ProjectConcentricRadialIntent import read_intents
from PlanarRendererInput import from_json, request_look
from ReadD01RootHistory import snapshot, observe_transition
from AuditConcentricDisplayState import compare_typed, ctext
from ProveVisualStateStore import detached_context, replay
from MakeVisualStateStore import visual_document
from para.concentric.MakeDisplayTree import DisplayListIntent, DisplayStateIntent
from Classes import registry
from Core import Obj
from defs.Visual import store_visual_states

from convert.adapters.solidworks.Archive.Construction.Assembly.Displays.AsmDisplayIn import AsmDisplayIn
from convert.adapters.solidworks.Archive.Construction.Circles.RadialLabelIn import RadialLabelIn
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.MakeCylAsm import MakeCylAsm
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import ReadStyleText
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.AssemblyPreparation.Concentric.PlanCylMate import PlanCylMate
from convert.adapters.solidworks.Core.AssemblyPreparation.Concentric.PrepCylChild import PrepCylChild
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import ReadAsmModel
from convert.adapters.solidworks.Core.AssemblyPreparation.Paths.ReadAsmPaths import ReadAsmPaths
from interchange.serialization.Deserialize import FromData


BASE = "43b419d5c2d5a4a90731c26f90a87eafaa1012bc"
BOUNDARY = "retained self context requires the actual earlier model of the same owned root and changed floating placement"


def verify_owned_edit(previous, current):
    before, after = (ReadAsmModel(value) for value in (previous, current))
    lead, follow = before.ChildDocument, after.ChildDocument
    boss, = lead.feature_timeline
    edited_boss, = follow.feature_timeline
    (depth_key,) = boss.parameter_ids
    old_depth, = (row for row in lead.parameters if row.id == depth_key)
    new_depth, = (row for row in follow.parameters if row.id == depth_key)
    parameters = tuple(replace(row, value=new_depth.value) if row is old_depth else row for row in lead.parameters)
    shifted = replace(lead, parameters=parameters, feature_timeline=(
        replace(boss, definition=replace(boss.definition, length=edited_boss.definition.length)),
    ))
    fixed = before.FixedIndex
    require(len(before.Occurrences) == len(after.Occurrences) == 2 and fixed == after.FixedIndex
            and len(before.GraphValue.documents) == len(after.GraphValue.documents) == 1
            and after.Occurrences[fixed] == before.Occurrences[fixed]
            and before.Occurrences[1 - fixed].transform != after.Occurrences[1 - fixed].transform
            and old_depth.value != new_depth.value and shifted == follow,
            BOUNDARY)
    instances = tuple(
        replace(old, transform=new.transform) for old, new in zip(before.Occurrences, after.Occurrences, strict=True)
    )
    embedded, = before.GraphValue.documents
    graph = replace(before.GraphValue, instances=instances, documents=(replace(embedded, document=shifted),))
    require(replace(previous, assembly=graph) == current, BOUNDARY)
    return before, after


def build(request, document, model):
    epoch, destination = request["written_at"], request["destination"]
    path = ReadAsmPaths(model.RootValue.name, model.ChildValue.name, destination, epoch)
    previous = build_arguments(request, document, model)
    serialized_label = request["radial_label"]
    label = RadialLabelIn(serialized_label["SketchId"], serialized_label["ParameterId"],
                          tuple(serialized_label["TextPoint"]))
    child = PrepCylChild(model.ChildDocument, path.ChildValue, request["child_scene"],
                         read_intents(request["child_lights"], epoch), LabelValue=label,
                         LookValue=from_json(request["appearance"]))
    plan = PlanCylMate(document, model.ChildDocument, child.CandidateValue, child.FaceTag)
    display = (AsmDisplayIn(request["root_display_name"], tuple((row.name, not row.hidden) for row in model.Occurrences)),)
    return MakeCylAsm(child.CandidateValue, previous[1], plan.Placements, plan.EndIndexes, child.FaceTag,
                      replace(plan.MateInput, LocalAxes=previous[-1].LocalAxes), DisplayValues=display)


def earlier_title(previous, current, owned):
    heads = tuple(value.HeaderValue.FieldsValue["f38"] for value in (previous, current))
    old, new = tuple(ReadFileKey(head) for head in heads)
    before_root = ReadNodeName(previous.StateValue.RootValue)
    active_root = ReadNodeName(current.StateValue.RootValue)
    models = previous.StateValue, current.StateValue
    require(previous is not current and old[0] == before_root and new[0] == active_root and before_root != active_root
            and new[1] and PureWindowsPath(new[1]).suffix.casefold() == ".sldasm"
            and old[2:] == new[2:] and new[2] == 3
            and all(ReadNodeName(value.CurrentConfig) == model.ConfigValue.name
                    for value, model in zip(models, owned, strict=True))
            and all(tuple(ReadNodeName(row) for row in value.OccurrenceValues) == tuple(row.name for row in model.Occurrences)
                    for value, model in zip((previous, current), owned, strict=True)),
            "retained self context requires a distinct earlier title and matching generated model owners")
    return ReadStyleText(before_root, "previous unlocated assembly title")


def relocate_visual(previous, current, owned, reg):
    former_title = earlier_title(previous, current, owned)
    config = current.StateValue.CurrentConfig.FieldsValue["f08"]
    selected = tuple(row.FieldsValue["f08"] for row in current.OccurrenceValues)
    display = DisplayListIntent(config, (DisplayStateIntent("Display State-1", tuple((key, True) for key in selected)),))
    source = visual_document(current.StateValue, (current.HeaderValue, current.TopHeader),
                             current.OccurrenceValues, display)
    baseline = store_visual_states(source, reg)
    require(baseline == current.StreamsValue[VISUAL], "shared neutral visual constructions disagree before history")
    old_alias = {"h10": Obj("moCStringHandle_c", {"f08": former_title}),
                 "h18": Obj("moCStringHandle_c", {"f08": ""})}
    refs = source.head["root"].FieldsValue["comps"]
    for row in refs:
        _, _, _, current_target, context = detached_context(row["comp"])
        fresh = context["shared"]
        require(all(current_target["f10"][key] is fresh[key] for key in old_alias),
                "previously unpooled context cannot retain another model title")
        context["shared"] = fresh | old_alias
    return store_visual_states(source, reg)


def compare_built(current, result, prior_title, reg):
    before = SldprtArchive.from_bytes(current.BytesValue)
    streams = dict(current.StreamsValue, **{VISUAL: result})
    output = BuildSldprt(streams, FormatVersion=4)
    after = SldprtArchive.from_bytes(output)
    require(before.streams.keys() == after.streams.keys()
            and {name for name in before.streams if before.require(name) != after.require(name)} == {VISUAL},
            "historical handle composition changed a live archive stream")
    first, first_summary = replay(before, reg)
    second, second_summary = replay(after, reg)
    differences, splits = compare_typed(first.head["root"], second.head["root"])
    _, merges = compare_typed(second.head["root"], first.head["root"])
    rows = tuple(detached_context(row["comp"]) for row in second.head["root"].FieldsValue["comps"])
    current_title, current_path, _, _ = ReadFileKey(current.HeaderValue.FieldsValue["f38"])
    live_refs = {row.FieldsValue["f08"]: row for row in current.OccurrenceValues}
    all_targets = tuple(ext["f10"] for _, _, _, ext, _ in rows)
    all_contexts = tuple(file["shared"] for _, _, _, _, file in rows)
    require(second_summary["terminal_map"] == first_summary["terminal_map"] + 2
            and second_summary["bytes"] - first_summary["bytes"] == 8 + len(prior_title.encode("utf-16-le"))
            and not merges and len(splits) == 2 and all(len(roles) == 2 for roles in splits.values())
            and len(differences) == 2
            and all("/f40/moExtObject_c/shared/" in path and
                    ("/h10/" in path or "/h18/" in path) for path in differences)
            and list(differences.values()) in ([[current_title, prior_title], [current_path, ""]],
                                               [[current_path, ""], [current_title, prior_title]]),
            "detached generated alias changed fields beyond the two exact pooled handle splits")
    require(all(ctext(row["h10"]) == current_title and ctext(row["h18"]) == current_path for row in all_targets)
            and all(ctext(row["h10"]) == prior_title and ctext(row["h18"]) == "" for row in all_contexts)
            and all(all_contexts[0][key] is all_contexts[1][key] for key in ("h10", "h18"))
            and all(context["f30"] == (101 + live_refs[feature].FieldsValue["f3f0"]) & 0xffffffff
                    for feature, context, _, _, _ in rows),
            "generated previous title displaced the actual current owner or stamp")
    return {"whole_parent_sha256": fingerprint(output),
            "current_parent_sha256": fingerprint(current.BytesValue), "unchanged_live_streams": len(streams) - 1,
            "baseline": first_summary, "with_history": second_summary,
            "historical_title": prior_title, "current_title": current_title,
            "alias_split_only": True, "generation_current_stamps": [row[1]["f30"] for row in rows],
            "alias_stream_growth": second_summary["bytes"] - first_summary["bytes"]}


def refuse(call, text):
    try:
        call()
    except ValueError as error:
        require(text in str(error), "unexpected ownership guard: " + str(error))
        return str(error)
    raise ValueError("unrelated root or stale context reached the alias generator")


def worker(request):
    require(set(request) == {"before", "after"}, "expect two independent neutral root snapshots")
    before, after = (FromData(request[stage]["document"]) for stage in ("before", "after"))
    before.assert_valid()
    after.assert_valid()
    reg = registry()
    audit = proof_guard()
    owned = verify_owned_edit(before, after)
    previous, current = (build(request[stage], document, model)
                         for stage, document, model in zip(("before", "after"), (before, after), owned, strict=True))
    result = compare_built(current, relocate_visual(previous, current, owned, reg),
                           request["before"]["root_model_name"], reg)
    selected = current.StateValue.CurrentConfig.FieldsValue["fce8"][1]["o"].FieldsValue["f10"].FieldsValue
    selected["f30"] -= 1
    try:
        stale = refuse(lambda: relocate_visual(previous, current, owned, reg), "measured fresh occurrence context")
    finally:
        selected["f30"] += 1
    foreign = replace(after, support_planes=tuple(reversed(after.support_planes)))
    require(not audit, "history generator attempted a writer read or launch")
    return {**result, "refusals": {
        "stale_current_stamp": stale,
        "same_current_as_previous": refuse(lambda: relocate_visual(current, current, owned, reg),
                                           "distinct earlier title and matching generated model owners"),
        "unrelated_root_datum_order": refuse(lambda: verify_owned_edit(before, foreign), BOUNDARY),
        "unchanged_edit": refuse(lambda: verify_owned_edit(after, after), BOUNDARY),
    }, "runtime_external_accesses": len(audit)}


def fresh_result(request):
    command = (sys.executable, "-I", "-B", str(HERE), "--worker")
    encoded = wire(request)
    first, second = (subprocess.run(command, input=encoded, capture_output=True, timeout=180) for _ in range(2))
    require(first.returncode == second.returncode == 0 and first.stdout == second.stdout,
            (first.stderr + second.stderr).decode() or "separate history workers disagree")
    return {"neutral_request_sha256": fingerprint(encoded), **json.loads(first.stdout)}


def inputs(disclosures):
    source = disclosures / "ConcentricMateSourcePacket02/Disclosed/D01"
    lock = json.loads(checked(source / "lock.json", LOCK))
    author = json.loads(checked(source / "author.json", AUTHOR))
    require(lock["source_locked"] and not lock["heldout_source_locked"] and author["result"]["passed"],
            "the exact D01 disclosed source lock is required")
    result, requests = {}, {}
    reg = registry()
    for (phase, pins), stage in zip(D01_LOCKED.items(), ("before", "after"), strict=True):
        directory = source / "Native" / phase
        require(pins == tuple(lock["native_artifacts"][phase.lower()][role]["sha256"] for role in ("parent", "child")),
                "D01 retained root is outside the original input custody")
        document, raw, shape = source_case(directory, *FILES, pins)
        start = json_digest(document)
        result[stage] = snapshot(document, raw, reg)
        design = project_d01(document, raw, shape)
        identity = result[stage]["header_file"]
        require(ctext(identity["h10"]) == design.settings.name and not document.bodies,
                "duplicate root title or separate standalone body")
        sketch, = design.child.document.sketches
        label = owned_label(shape.native.LinkValue)
        look, _ = request_look(SldprtArchive.from_bytes(checked(directory / FILES[1], pins[1])), reg)
        look = replace(from_json(look), StartAppearanceId=1)
        target = str(PureWindowsPath(r"C:\KitD01RootHistory") / phase / FILES[0])
        requests[stage] = {**model_request(design, EPOCH, target),
                           "radial_label": asdict(RadialLabelIn(sketch.id, sketch.parameter_ids[0], label["text"])),
                           "appearance": asdict(look)}
        require(start == json_digest(document), "inspection changed the original retained read")
        result[stage]["public_document_sha256"] = start
        result[stage]["native_files_sha256"] = pins
    history = observe_transition(result["before"], result["after"])
    for row in result.values():
        del row["header_file"], row["contexts"]
    return result, history, requests


def main():
    parser = ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--worker", action="store_true")
    mode.add_argument("--disclosures", type=Path)
    args = parser.parse_args()
    if args.worker:
        sys.stdout.buffer.write(wire(worker(json.load(sys.stdin))))
        return
    source, history, requests = inputs(args.disclosures)
    original = fresh_result(requests)
    variant = {stage: {**request, "root_model_name": title} for (stage, request), title in
               zip(requests.items(), ("Initial independent frame", "Assigned edited frame"), strict=True)}
    varied = fresh_result(variant)
    require(original["historical_title"] == history["previous_model_name"] and
            original["current_title"] == history["current_model_name"]
            and varied["historical_title"] == variant["before"]["root_model_name"]
            and varied["current_title"] == variant["after"]["root_model_name"]
            and varied["alias_stream_growth"] != original["alias_stream_growth"],
            "independent title contrast failed to produce its own wire size")
    receipt = {"schema": "kit.sw2026.d01-root-history.v1", "base": BASE, "source_build": "34.5.2.0604",
               "source": source, "native_transition": history, "generated": original, "independent_title": varied,
               "source_lock_sha256": LOCK, "source_author_sha256": AUTHOR, "guarded_workers": 4,
               "oracle_launches": 0, "heldout_reads": 0, "public_admission": False, "whole_source_approved": False,
               "source_hashes": {str(path.relative_to(REPO)): fingerprint(path.read_bytes())
                                 for path in (HERE, HERE.with_name("ReadD01RootHistory.py"))}}
    print(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
