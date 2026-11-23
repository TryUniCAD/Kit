from argparse import ArgumentParser
from dataclasses import asdict, replace
import json
from pathlib import Path, PureWindowsPath
import subprocess
import sys


HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from ProveD01RootHistory import build, earlier_title, inputs, relocate_visual, verify_owned_edit, wire
from ProveD01ConcentricBridge import FILES, REPO, VISUAL, fingerprint, model_request, proof_guard
from ProveD01ChildAppearance import EPOCH
from ProveD01ParentDisplay import build_arguments
from ProveD01RadialLabel import owned_label
from ProveConcentricSourceBrep import checked, source_case
from ProjectD01Concentric import project_d01, require
from ProveVisualStateStore import detached_context, replay
from AuditConcentricDisplayState import compare_typed, file_signature
from ReadD01RootHistory import file_identity, handle_alias
from ReadConcentricCmgrInputs import (
    CMGR, MANAGER_HEADER, HAS_CHILD_VIEW, ChildViewIntent, child_display, child_directory,
    config_owner, contextual_rows, manager_root_stamps, owned_source,
)
from PlanarRendererInput import from_json, request_look
from Classes import registry
from ConcentricSourcePlan import disclosed_cases

from convert.adapters.solidworks.Archive.Construction.Assembly.EmitAsmStreams import EmitAsmStreams
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakeFileHandle import MakeFileHandle
from convert.adapters.solidworks.Archive.Construction.Circles.RadialLabelIn import RadialLabelIn
from convert.adapters.solidworks.Archive.Construction.Part.Displays.CheckSelfVisual import CheckSelfVisual
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Assembly.Assembly import XmlRoot
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName, ReadRows
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import ReadAsmModel
from convert.adapters.solidworks.Core.AssemblyPreparation.Concentric.ReadConcMate import ReadConcMate
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.serialization.Deserialize import FromData


BASE = "6d85ed1cb9ff6c033c5a0017dbfc49ffb52bc146"
CORPUS = "3c67d10789bbd681bfb99da712e1c6a035d78713b326c3048373ed4972198997"
ROOT_RECEIPT = "b3553f47a136e36f36e367d56362c84d48ea66418e72e43e0af71e54d2e17bbd"
CFG = "Contents/Config-0"
INSTANCE = "swXmlContents/COMPINSTANCETREE"


def refuse(call, match):
    try:
        call()
    except ValueError as error:
        require(match in str(error), "unexpected ownership refusal: " + str(error))
        return str(error)
    raise ValueError("foreign saved context model was emitted")


def selection_plan(current, model, payload, reg):
    child = current.ChildValue
    CheckSelfVisual(child)
    archive = SldprtArchive.from_bytes(child.BytesValue)
    config = config_owner(archive, "moPartConfiguration_c")
    name, display_name, display_key = child_display(archive, config, reg)
    require(child.SelfView is not None and child.SelfView.StateName == display_name
            and config.FieldsValue["f08"] == child.CurrentConfig.FieldsValue["f08"]
            and name == ReadNodeName(child.CurrentConfig),
            "neutral selection lacks its actual generated child display owner")
    supplied = tuple(ChildViewIntent(**row) for row in payload)
    expected = tuple(ChildViewIntent(row.id, row.configuration_name, display_name)
                     for row in model.Occurrences[::-1])
    require(supplied == expected and all(row.configuration_name == name for row in expected),
            "neutral selection differs from its actual ordered occurrence, configuration or child display")
    return name, display_name, display_key


def apply_history(previous, current, owned, selection):
    prior_title = earlier_title(previous, current, owned)
    old_model, new_model = owned
    config = current.StateValue.CurrentConfig
    target = current.HeaderValue.FieldsValue["f38"].FieldsValue["shared"]
    history = target | {"h10": MakeFileHandle(prior_title), "h18": MakeFileHandle("")}
    rows = tuple(contextual_rows(config))[::-1]
    headers = tuple(bundle.HeaderValue.FieldsValue["f38"].FieldsValue["shared"] for bundle in (previous, current))
    require(file_signature(headers[0]) == file_signature(headers[1]),
            "history spans different parent creation owners")
    for old, new, old_inst, new_inst, (key, state, context, ext, file) in zip(
        previous.OccurrenceValues, current.OccurrenceValues, old_model.Occurrences, new_model.Occurrences, rows,
        strict=True,
    ):
        before, after = old.FieldsValue, new.FieldsValue
        prior_stamp = before["f3f0"]
        require(old_inst.id == new_inst.id and before["f08"] == after["f08"] == ext["f44"] == key
                and before["f3f0"] == after["f3f0"]
                and context["f30"] == (101 + prior_stamp) & 0xffffffff
                and ext["f10"] is target and after["f4f8"].FieldsValue["f10"] is target
                and file["shared"] is target
                and state["f28"] == after["f3c0"] == {
                    "f08": selection[0], "f10": current.ChildValue.CurrentConfig.FieldsValue["f08"]}
                and after["f4f8"].FieldsValue["f50"] is new
                and state["f18"] == 0x111,
                "history placement requires actual fresh predecessor/current references and selected configuration")
        opts = state["f08"].FieldsValue
        require((opts["f48"], opts["f50"], opts["f64"]) == ("", -1, 0),
                "fresh component selection unexpectedly contains another display owner")
        after["f3f0"] = (prior_stamp + int(old_inst.transform != new_inst.transform)) & 0xffffffff
        state["f18"] |= HAS_CHILD_VIEW
        opts.update(f48=selection[1], f50=selection[2])
        file["shared"] = history


def verify_current(current, composed, historical_title, reg):
    archive = SldprtArchive.from_bytes(composed)
    child = SldprtArchive.from_bytes(current.ChildValue.BytesValue)
    lnk = ReadNativeLink(archive, 0)
    child_link = ReadNativeLink(child, 0)
    header = lnk.ConfigValue.HeaderValue
    root = lnk.ConfigValue.RootValue
    current_file = header.FieldsValue["f38"].FieldsValue["shared"]
    refs = tuple(row["o"] for row in ReadRows(root.FieldsValue["f68"]["list"]["items"]))
    top = ReadHeaderGraph(archive.require("Header2"), 19000)
    _, child_stamps = child_directory(lnk, (header, top), child, child_link, refs)
    config = config_owner(archive, "moConfiguration_c")
    root_stamps = manager_root_stamps(archive, root, config, refs)
    child_config = config_owner(child, "moPartConfiguration_c")
    selected = child_display(child, child_config, reg)
    doc, visual_summary = replay(archive, reg)
    vis = tuple(detached_context(row["comp"]) for row in doc.head["root"].FieldsValue["comps"])
    xml = {int(node.attrib["swID"]): int(node.attrib["swTransformStamp"])
           for node in XmlRoot(archive.require(INSTANCE)).iter() if node.tag.rsplit("}", 1)[-1] == "swReference"}
    rows, contexts = [], []
    for (key, state, ctx, ext, file), reference, visual in zip(contextual_rows(config), refs[::-1], vis, strict=True):
        field = reference.FieldsValue
        live = field["f4f8"].FieldsValue
        features = field["f08"] == key == live["f44"] == visual[0] and live["f50"] is reference
        stamps = tuple(field[key] for key in ("f3e0", "f3e8", "f3f4"))
        opts = state["f08"].FieldsValue
        require(features and stamps == child_stamps[:3] and field["f3f8"] == 101
                and file_identity(ext["f10"]) == file_identity(live["f10"]) == file_identity(current_file)
                and file_identity(visual[3]["f10"]) == file_identity(current_file)
                and file_identity(file["shared"]) == file_identity(visual[4]["shared"])
                == (file_signature(current_file), historical_title, "")
                and handle_alias(file["shared"], ext["f10"]) == (False, False)
                and ctx["f30"] == visual[1]["f30"]
                and xml[key] == field["f3f0"]
                and state["f18"] == 0x111 | HAS_CHILD_VIEW
                and (opts["f48"], opts["f50"]) == selected[1:] and opts["f64"] == 0
                and state["f28"] == field["f3c0"] == {"f08": selected[0], "f10": child_config.FieldsValue["f08"]},
                "generated current reference, selected child or historical context failed its actual archive join")
        contexts.append((ext["f10"], file["shared"]))
        rows.append({"occurrence_id": key, "name": ReadNodeName(reference),
                     "current_placement": field["f3f0"], "manager_stamp": ctx["f30"],
                     "child_display": list(selected[1:]), "before_child_clock_used_for_live": False})
    require(sorted(row["current_placement"] + 101 - row["manager_stamp"] for row in rows) == [0, 1]
            and all(handle_alias(a, b) == (True, True) for a, b in zip(*contexts, strict=True)),
            "historical contexts no longer have one observed placement edit and pooled owner pairs")
    return rows, visual_summary, root_stamps


def manager_delta(old, new, selection):
    graphs = tuple(ReadCmgrMut(data, 19000) for data in (old, new))
    forward, splits = compare_typed(*(graph.RootValue for graph in graphs))
    _, merges = compare_typed(*(graph.RootValue for graph in graphs[::-1]))
    scalar_leaves = {
        tail: [values for path, values in forward.items() if path.endswith(tail)]
        for tail in ("moConfigObject_c/f18", "moConfig_c/f48", "moConfig_c/f50")
    }
    alias_leaves = [path for path in forward if "/f40/moExtObject_c/shared/h" in path]
    require(len(forward) == 8 and len(alias_leaves) == 2 and not merges and len(splits) == 2
            and all(len(targets) == 2 for targets in splits.values())
            and scalar_leaves == {
                "moConfigObject_c/f18": [[0x111, 0x111 | HAS_CHILD_VIEW]] * 2,
                "moConfig_c/f48": [["", selection[1]]] * 2,
                "moConfig_c/f50": [[-1, selection[2]]] * 2,
            },
            "CMgr history changed beyond two state assignments and two shared historical handles")
    return {"before_bytes": len(old), "after_bytes": len(new), "exact_changed_typed_leaves": len(forward),
            "split_handle_aliases": len(splits)}


def worker(request):
    require(set(request) == {"before", "after", "selected_child_views"}, "saved CMgr requires a complete neutral request")
    docs = tuple(FromData(request[key]["document"]) for key in ("before", "after"))
    for document in docs:
        document.assert_valid()
    reg = registry()
    audit = proof_guard()
    owned = verify_owned_edit(*docs)
    previous, current = (build(request[key], document, model)
                         for key, document, model in zip(("before", "after"), docs, owned, strict=True))
    model = owned[1]
    selection = selection_plan(current, model, request["selected_child_views"], reg)
    altered = [{**row, "display_name": "foreign child state"} for row in request["selected_child_views"]]
    different_config = [{**row, "configuration_name": "foreign child config"} for row in request["selected_child_views"]]
    refusals = {
        "wrong_child_display": refuse(lambda: selection_plan(current, model, altered, reg), "actual ordered occurrence"),
        "wrong_child_configuration": refuse(lambda: selection_plan(current, model, different_config, reg),
                                            "actual ordered occurrence"),
        "swapped_occurrences": refuse(lambda: selection_plan(current, model, request["selected_child_views"][::-1], reg),
                                      "actual ordered occurrence"),
    }
    expected_state = relocate_visual(previous, current, owned, reg)
    recipe = build_arguments(request["after"], docs[1], model)[1]
    child_before = current.ChildValue.BytesValue
    apply_history(previous, current, owned, selection)
    streams = EmitAsmStreams(current.StateValue, current.ChildValue, recipe, (current.HeaderValue, current.TopHeader),
                             current.OccurrenceValues, current.MateValues).StreamsValue
    streams[VISUAL] = expected_state
    before = current.StreamsValue
    changed = {key for key in before.keys() | streams.keys() if before.get(key) != streams.get(key)}
    require(changed == {CMGR, MANAGER_HEADER, CFG, INSTANCE, VISUAL},
            "saved placement altered an unrelated archive stream: " + repr(changed))
    manager_changes = manager_delta(before[CMGR], streams[CMGR], selection)
    result = BuildSldprt(streams, FormatVersion=4)
    rows, visual, root_stamps = verify_current(current, result, request["before"]["root_model_name"], reg)
    require(not audit and current.ChildValue.BytesValue == child_before,
            "saved CMgr generator attempted external access or replaced the owned child")
    return {"parent_sha256": fingerprint(result), "parent_bytes": len(result), "child_sha256": fingerprint(current.ChildValue.BytesValue),
            "fresh_parent_sha256": fingerprint(current.BytesValue), "changed_parent_streams": sorted(changed),
            "unchanged_parent_streams": len(streams) - len(changed), "child_unchanged": True, "linked_contexts": rows,
            "visual_replay": visual, "manager_transform_and_geometry": root_stamps, "manager_delta": manager_changes,
            "refusals": refusals, "runtime_accesses": len(audit)}


def control(request):
    document = FromData(request["document"])
    document.assert_valid()
    model = ReadAsmModel(document)
    _, _, _, alignment, locked = ReadConcMate(model)
    require(alignment == 2 or locked, "control was silently normalized to aligned and unlocked")
    audit = proof_guard()
    refusal = refuse(lambda: build(request, document, model),
                     "assembly visibility requires one actual aligned unlocked concentric mate")
    require(not audit, "contrast generation attempted external access")
    return {"refusal": refusal, "alignment_code": alignment, "rotation_locked": locked, "runtime_accesses": len(audit)}


def demonstrate_scope(projected, child, shape, parent_name, phase, reg):
    target = str(PureWindowsPath(r"C:\KitConcentricCmgrContrast") / phase / parent_name)
    neutral = model_request(projected, EPOCH, target)
    sketch, = projected.child.document.sketches
    label = owned_label(shape.native.LinkValue)
    look, _ = request_look(child, reg)
    request = {
        **neutral,
        "radial_label": asdict(RadialLabelIn(sketch.id, sketch.parameter_ids[0], label["text"])),
        "appearance": asdict(replace(from_json(look), StartAppearanceId=1)),
    }
    command = (sys.executable, "-I", "-B", str(HERE), "--control")
    result = subprocess.run(command, input=wire(request), capture_output=True, timeout=180)
    require(result.returncode == 0, result.stderr.decode())
    return json.loads(result.stdout)


def disclose(disclosures):
    reports = REPO / "re/solidworks/measurements/2026"
    proof = json.loads(checked(reports / "ConcentricMateSourceArchive01.json", CORPUS))["cases"]
    design = disclosures / "ConcentricMateSourcePacket02/Disclosed"
    results, d01_selections = {}, {}
    reg = registry()
    for case in disclosed_cases():
        slot = case["id"]
        info = proof[slot]
        require(info["heldout_source_locked"] is False, "only disclosed native mate controls are permitted")
        names = case["name"] + ".SLDASM", case["child_name"] + ".SLDPRT"
        results[slot] = {}
        for stage, phase in (("before", "Source"), ("after", "Edited")):
            pins = tuple(info["native_artifact_digests"][phase.lower()][role]["sha256"] for role in ("parent", "child"))
            path = design / slot / "Native" / phase
            doc, raw, shape = source_case(path, *names, pins)
            projected = project_d01(doc, raw, shape)
            parent, child = SldprtArchive.from_bytes(raw), SldprtArchive.from_bytes(checked(path / names[1], pins[1]))
            selection, receipt = owned_source(doc, parent, child, pins[1], reg, dict(projected.identities["occurrences"]))
            require(receipt["alignment"] == ("anti_aligned" if case["api_alignment"] == 1 else "aligned")
                    and receipt["rotation_locked"] is case["lock_rotation"],
                    "source lock and signed alignment differ from the independent authors")
            result = {**receipt, "native_pair_sha256": pins, "semantic_selections": selection}
            if slot == "D01":
                d01_selections[stage] = selection
            else:
                result["full_construction_refusal"] = demonstrate_scope(projected, child, shape, names[0], phase, reg)
            results[slot][stage] = result
    require(d01_selections["before"] == d01_selections["after"], "actual D01 child presentation assignment changed during edit")
    return results, d01_selections["after"]


def main():
    parser = ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--worker", action="store_true")
    mode.add_argument("--control", action="store_true")
    mode.add_argument("--disclosures", type=Path)
    args = parser.parse_args()
    if args.worker:
        sys.stdout.buffer.write(wire(worker(json.load(sys.stdin))))
        return
    if args.control:
        sys.stdout.buffer.write(wire(control(json.load(sys.stdin))))
        return
    reports = REPO / "re/solidworks/measurements/2026"
    prior = json.loads(checked(reports / "ConcentricD01RootHistory01.json", ROOT_RECEIPT))
    source_audit, selection = disclose(args.disclosures)
    _, hist, request = inputs(args.disclosures)
    request["selected_child_views"] = selection
    data = wire(request)
    command = (sys.executable, "-I", "-B", str(HERE), "--worker")
    first, second = (subprocess.run(command, input=data, capture_output=True, timeout=180) for _ in range(2))
    require(first.returncode == second.returncode == 0 and first.stdout == second.stdout,
            (first.stderr + second.stderr).decode() or "independent saved CMgr workers disagree")
    output = json.loads(first.stdout)
    require(output["fresh_parent_sha256"] == prior["generated"]["current_parent_sha256"]
            and output["visual_replay"]["sha256"] == prior["generated"]["with_history"]["sha256"]
            and hist == prior["native_transition"],
            "new saved-context composition changed the previously verified fresh and detached graph origins")
    report = {"schema": "kit.sw2026.saved-concentric-cmgr.v1", "base": BASE, "corpus_receipt_sha256": CORPUS,
              "prior_root_receipt_sha256": ROOT_RECEIPT, "disclosed_parents": source_audit,
              "neutral_request_sha256": fingerprint(data), "generated": output, "guarded_writers": 2,
              "guarded_lock_and_alignment_refusals": 4,
              "native_runs": 0, "heldout_reads": 0, "whole_source_admitted": False, "public_publication": False,
              "source_sha256": {str(path.relative_to(REPO)): fingerprint(path.read_bytes())
                                for path in (HERE, HERE.with_name("ReadConcentricCmgrInputs.py"))}}
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
