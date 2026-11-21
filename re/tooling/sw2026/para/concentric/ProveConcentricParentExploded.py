import argparse
import codecs
from dataclasses import asdict, replace
import json
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[5]
SW2026 = REPO / "re/tooling/sw2026"
sys.path[:0] = [str(REPO), str(REPO / "src"), str(SW2026), str(SW2026 / "serial")]

from CheckConcentricSourceBrep import map_source_endpoints
from convert import open_document
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.solidworks.Archive.Construction.Assembly.Headers.MakeAsmHeaders import MakeAsmHeaders
from convert.adapters.solidworks.Archive.Construction.Assembly.MakeAsmBase import MakeAsmBase
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.PutPartRefsMut import PutPartRefsMut
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.MakeAsmKeys import MakeAsmKeys
from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import FeatureInstant
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, RequireNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import ReadAsmModel
from convert.adapters.solidworks.Core.Native import ParseKeywords
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadMemberTime import ReadMemberTime
from convert.adapters.solidworks.Core.TypedResolved.Presentation.SystemState import ReadSystemState
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.serialization.Deserialize import FromData
from para.concentric.ProjectConcentricRadialIntent import read_intents
from para.concentric.ProveConcentricParentLights import EPOCH, ROOT_NAME, SEED, digest, disclose, nested_regressions
from para.concentric.ProveConcentricParentLights import public_light_rows, read_scene, with_lights
from para.concentric.ProveConcentricParentNotes import CHILD, CONFIG, EMPTY_SYSTEM, KEYWORDS, LIGHT_ONLY
from para.concentric.ProveConcentricParentNotes import observe, read_notes, rejected, with_notes
from para.concentric.ProveConcentricSourceBrep import D01_LOCKED, RADIAL_LOCKED, checked, json_digest, require, source_case
from para.concentric.ProveSignedConcentricWriter import emit_parts, inventory_receipt, neutral_d01, plan_bundle
from para.concentric.ProveSignedConcentricWriter import source_inventory, verify_legacy, verify_parts


BASELINE = "b791b65c8dea2fc0c486aa0b47eea97ece4d9ce9"
TOOL = "re/tooling/sw2026/para/concentric/ProveConcentricParentExploded.py"
SCOPE = (
    "Assembly/AssemblySysIn.py", "Assembly/System/MakeAsmSysMut.py", "Assembly/System/MakeAsmExploded.py",
    "Assembly/System/CheckAsmMembers.py", "Nodes/InitNodeMut.py", "Assembly/Xml/AsmKeyNodes.py",
    "Assembly/Xml/AsmXmlRoles.py", "Assembly/Xml/AsmExplodeNode.py",
    "Assembly/Xml/AsmKeywordName.py", "Assembly/Xml/MakeAsmKeys.py", "NestedAssemblies/MakeNestedKeys.py",
)
CLASS = "moExplViewManager_c"
ROLE = "Exploded Views"
PRIOR_NOTES = "f0384f8120977e0538e506349d75e214ca8694484adff4cb3aa1bcc2060aca8e"


def read_manager(link, present):
    config, resolved = link.ConfigValue, link.ResolvedValue
    require(link.ConfigName == CONFIG and all(
        row.get("completed") and not row.get("missing_schemas") and not row.get("provisional_schemas")
        for row in (config.ReportValue, resolved.ReportValue)
    ), "complete typed assembly configuration and resolved map are required")
    root = RequireNode(config.RootValue, "moAssembly_c")
    require(FieldInt(root.FieldsValue, "f1598") == 0, "assembly has unmapped exploded placement state")
    manager = root.FieldsValue["f1590"]
    require((manager is not None) == present, "assembly direct exploded manager presence differs")
    require(not any(row.ClassValue.NameValue == CLASS for row in resolved.RootsValue),
            "assembly exploded manager has an unexpected separate resolved root")
    for archive in (config, resolved):
        found = tuple(row.EntryValue for row in archive.MapValue.EntriesValue
                      if isinstance(row.EntryValue, ArchiveNode) and row.EntryValue.ClassValue.NameValue == CLASS)
        require(found == ((manager,) if present else ()), "assembly exploded manager is not the same unique linked map node")
    if not present:
        return None
    values = RequireNode(manager, CLASS).FieldsValue
    require(manager.ClassValue.SchemaValue == 1 and 0 < FieldInt(values, "f08") < FieldInt(config.HeaderValue.FieldsValue, "f08")
            and not any(FieldInt(row.FieldsValue, "f08") == values["f08"] for row in resolved.RootsValue),
            "assembly exploded manager requires the actual allocated schema-one identity")
    require(all(key in values and values[key] == value for key, value in {
        "f18": None, "f358": None, "f360": None, "f398": 0.0, "f3a0": -1, "f3a4": -1, "f368": {"n": 0, "items": []},
        "f60": {"list": {"n": 0, "items": []}, "tail": 0}, "hidden": 0,
    }.items()), "assembly exploded manager carries unsupported contents or placement state")
    return manager


def placement_state(manager):
    return {key: ReadSystemState(value) for key, value in manager.FieldsValue.items()
            if key not in ("f08", "f2a0", "f2a4", "f301")}


def check_index(document, archive, manager):
    manager_id = FieldInt(manager.FieldsValue, "f08") if manager is not None else None
    _, words = ParseKeywords(archive.require(KEYWORDS))
    raw_rows = [row for row in words if row.kind == ROLE or row.object_id == manager_id]
    rows = [row for row in document.feature_timeline
            if row.attributes["native_type"] == ROLE or row.attributes["native_object_id"] == manager_id]
    if manager is None:
        require(not raw_rows and not rows, "assembly exploded name was indexed without an actual object")
        return None
    expected = {"id": str(manager_id), "Name": "", "Type": ROLE}
    require(len(raw_rows) == len(rows) == 1 and raw_rows[0].xml_tag == rows[0].attributes["xml_tag"] == "Feature"
            and raw_rows[0].properties == rows[0].attributes["native_properties"] == expected
            and raw_rows[0].object_id == rows[0].attributes["native_object_id"] == manager_id
            and not raw_rows[0].dimensions and rows[0].name == f"{ROLE} {manager_id}",
            "exploded manager index must carry one real nameless owner")
    return {"role": ROLE, "id": manager_id, "native_name": "", "reader_name": rows[0].name}


def observe_manager(document, payload, present):
    archive = SldprtArchive.from_bytes(payload)
    node = read_manager(ReadNativeLink(archive, 0), present)
    index = check_index(document, archive, node)
    result = {"raw_and_public_keyword": index, "total_feature_rows": len(document.feature_timeline)}
    if node is not None:
        state = placement_state(node)
        clock = () if not any(FieldInt(node.FieldsValue, key) for key in ("f2a0", "f2a4")) else asdict(ReadMemberTime(node))
        result.update({"manager_class": CLASS, "clock": clock or None, "typed_common_field_count": len(state),
                       "creation_subservice_pack": FieldInt(node.FieldsValue, "f301"),
                       "typed_common_state_sha256": digest(json.dumps(state, sort_keys=True, allow_nan=False).encode()),
                       "config_map_entries": 1, "resolved_map_entries": 1, "resolved_roots": 0})
        return state, result
    return None, result


def with_exploded(bundle, value):
    attachment, mate, settings, poses = bundle
    return attachment, mate, replace(settings, SystemValue=replace(settings.SystemValue, HasEmptyExplodedView=value)), poses


def refusal_cases(bundle, raw):
    def mutate_source(phase, field, value):
        link = ReadNativeLink(SldprtArchive.from_bytes(raw), 0)
        manager = read_manager(link, True)
        owner = link.ConfigValue.RootValue if phase == "root" else manager
        owner.FieldsValue[field] = value
        return read_manager(link, True)

    def mutate_emitter(change):
        attachment, _, metadata, placements = bundle
        state = MakeAsmBase(metadata)
        headers = MakeAsmHeaders(state, metadata)
        references = PutPartRefsMut(state, attachment.candidate, metadata, placements, headers)
        manager = state.RootValue.FieldsValue["f1590"]
        features = state.FeatureValues
        if change == "foreign_owner":
            manager.FieldsValue["owner"] = features[0]
        elif change == "flat_resolved_root":
            state = replace(state, FeatureValues=(*features, manager))
        elif change == "duplicate_feature_id":
            manager.FieldsValue["f08"] = features[0].FieldsValue["f08"]
        elif change == "unexpected_name":
            manager.FieldsValue["f18"] = features[0].FieldsValue["f18"]
        elif change == "active_placement":
            manager.FieldsValue["f360"] = features[0]
        elif change == "foreign_class":
            state.RootValue.FieldsValue["f1590"] = features[0]
        else:
            raise AssertionError(change)
        return MakeAsmKeys(state, headers[0], attachment.candidate, references)

    source = rejected({
        "unexpected_placement_flags": lambda: mutate_source("root", "f1598", 1),
        "missing_actual_manager": lambda: mutate_source("root", "f1590", None),
        "active_placement_record": lambda: mutate_source("manager", "f360", False),
        "populated_explosion_map": lambda: mutate_source("manager", "f368", {"n": 1, "items": [{"k": 1, "v": None}]}),
        "positive_explode_index": lambda: mutate_source("manager", "f3a0", 1),
    })
    writer = rejected({
        "invalid_presence": lambda: with_exploded(bundle, 1),
        **{name: lambda name=name: mutate_emitter(name) for name in (
            "foreign_owner", "flat_resolved_root", "duplicate_feature_id", "unexpected_name", "active_placement", "foreign_class",
        )},
    })
    return {"source": source, "writer": writer}


def build(neutral, axes, light_caption, lights, cabinet, source_notes):
    GetDocumentCaps(ReadAsmModel(neutral).ChildDocument)
    for encoding in ("utf-8", "utf-16-le", "utf-16-be", "cp1252"):
        codecs.lookup(encoding)
    notes = replace(source_notes, HeadCreated=FeatureInstant(EPOCH + len(lights), 1),
                    EndCreated=FeatureInstant(EPOCH + len(lights), 2))
    denied = []

    def guard(event, _):
        if active and event in {"open", "subprocess.Popen", "os.system", "os.posix_spawn", "os.fork", "socket.connect"}:
            denied.append(event)
            raise RuntimeError("assembly exploded manager made a runtime access: " + event)

    active = True
    sys.addaudithook(guard)
    try:
        bare = plan_bundle(neutral, EPOCH)
        light_bundle = with_lights(bare, light_caption, lights)
        prior = with_notes(light_bundle, cabinet, notes)
        request = with_exploded(prior, True)
        parent = emit_parts(request, axes)
        child = request[0].file_bytes
        second = with_exploded(with_notes(with_lights(plan_bundle(neutral, EPOCH), light_caption, lights), cabinet, notes), True)
        require(parent == emit_parts(second, axes) and child == second[0].file_bytes,
                "separate from-neutral exploded manager construction did not repeat")
        before = emit_parts(with_exploded(prior, False), axes)
        require(digest(before) == PRIOR_NOTES and digest(emit_parts(light_bundle, axes)) == LIGHT_ONLY
                and digest(emit_parts(bare, axes)) == EMPTY_SYSTEM and digest(child) == CHILD,
                "an explicit absent or default assembly changed existing output")
        baseline = SldprtArchive.from_bytes(before)
        read_manager(ReadNativeLink(baseline, 0), False)
        archive = SldprtArchive.from_bytes(parent)
        link = ReadNativeLink(archive, 0)
        node = read_manager(link, True)
        _, scene_members, observed = read_scene(link)
        note_cabinet, note_members, built_notes = read_notes(link, 2)
        require(built_notes == notes and observed == lights, "assembly exploded manager changed another presentation owner")
        before_link = ReadNativeLink(baseline, 0)
        _, old_scene_members, _ = read_scene(before_link)
        _, old_note_members, _ = read_notes(before_link, 2)
        require(tuple(row.FieldsValue["f08"] for row in (*scene_members, *note_members)) ==
                tuple(row.FieldsValue["f08"] for row in (*old_scene_members, *old_note_members)),
                "assembly exploded manager changed existing member identities")
        require(all(FieldInt(node.FieldsValue, key) == 0 for key in ("f2a0", "f2a4")),
                "fresh exploded manager requires its independently measured unset clock")
        sizes = [len(value.require(CONFIG)) for value in (baseline, archive)]
        require(sizes[1] > sizes[0], "the Config stream must grow with the real optional owner")
        simple = SldprtArchive.from_bytes(emit_parts(with_exploded(bare, True), axes))
        simple_link = ReadNativeLink(simple, 0)
        read_manager(simple_link, True)
        read_scene(simple_link, empty=True)
        read_notes(simple_link, 0)
        exact = verify_parts(parent, request, axes)
    finally:
        active = False
    require(not denied, "assembly exploded manager used implicit inputs")
    generated = {"parent_sha256": digest(parent), "child_sha256": digest(child), "config_before_after_bytes": sizes,
                 "changed_streams": sorted(key for key in archive.streams if archive.require(key) != baseline.require(key)),
                 "linked_mate_readback": exact, "guarded_repeats": 2, "runtime_file_process_network_attempts": len(denied),
                 "previous_notes_parent_sha256": digest(before), "presence_without_notes_or_lights": True}
    return parent, child, node, scene_members, generated, request


def main():
    parser = argparse.ArgumentParser(description="Measure the bounded direct empty exploded-view manager")
    parser.add_argument("disclosed_root", type=Path)
    parser.add_argument("prior_source_closure", type=Path)
    parser.add_argument("new_scratch", type=Path)
    args = parser.parse_args()
    before = source_inventory(args.prior_source_closure)
    after = source_inventory(REPO)
    delta = {name for name in set(before) | set(after) if before.get(name) != after.get(name)}
    prefix = "src/convert/adapters/solidworks/Archive/Construction/"
    require(delta == {TOOL, *(prefix + path for path in SCOPE)}, "proof code differs from the scoped exploded-view overlay")
    base = args.disclosed_root.resolve()
    d01 = base / "ConcentricMateSourcePacket02/Disclosed/D01"
    lock = json.loads(checked(d01 / "lock.json", "bdd8bf3782ccf01991a3ac402da2923f2d320728792fb8ccb500f73189e9f90b"))
    require(lock["source_locked"] and not lock["heldout_source_locked"], "D01 must remain the only source closure")
    d01_names = ("ConcentricD01AlignedFree.SLDASM", "ConcentricD01Child.SLDPRT")
    radial_names = ("RadialConcentricProbe.SLDASM", "DisclosedRadialSceneProbe.SLDPRT")
    inputs = (
        ("D01Source", d01 / "Native/Source", d01_names, D01_LOCKED["Source"]),
        ("D01Edited", d01 / "Native/Edited", d01_names, D01_LOCKED["Edited"]),
        ("RadialSaved", base / "RadialConcentric01/Working", radial_names, RADIAL_LOCKED["Working"]),
        ("RadialFrozen", base / "RadialConcentric01/Frozen", radial_names, RADIAL_LOCKED["Frozen"]),
    )
    source, raw, shape, light_caption, light_intents, _ = disclose(*inputs[0])
    source_state, original = observe_manager(source, raw, True)
    require(original["creation_subservice_pack"] == 0, "original manager has unexpected creation provenance")
    source_notes, note_receipt = observe(source, raw, 2)
    layouts = [{"case": inputs[0][0], **original}]
    for label, folder, names, hashes in inputs[1:]:
        item, payload, _ = source_case(folder, *names, hashes)
        has_manager = label != "RadialFrozen"
        state, receipt = observe_manager(item, payload, has_manager)
        if has_manager:
            require(state == source_state, "independent disclosures disagree on empty manager state")
            require(receipt["clock"] == (original["clock"] if label == "D01Edited" else None),
                    "source edit or independent native default creation clock differed")
            require(receipt["creation_subservice_pack"] == original["creation_subservice_pack"],
                    "independent disclosed creation subservice differed")
        layouts.append({"case": label, **receipt})
    axes_owner = map_source_endpoints(source, raw, shape, shape)
    axes = tuple(row["local_axis"] for row in axes_owner)
    seed = FromData(json.loads(checked(REPO / "re/solidworks/inputs/ConcentricFeatureNeutral01.json", SEED)))
    neutral = neutral_d01(seed, source, axes_owner, shape, ROOT_NAME)
    lights = read_intents(light_intents, EPOCH)
    parent, child, manager, light_members, emission, request = build(
        neutral, axes, light_caption, lights, note_receipt["annotation_keyword_rows"][0][1], source_notes)
    require(placement_state(manager) == source_state, "generated typed empty manager differs from independent disclosures")
    out = args.new_scratch.resolve()
    out.mkdir()
    native_parent = out / (ROOT_NAME + ".SLDASM")
    native_parent.write_bytes(parent)
    (out / "D01SignedChild.SLDPRT").write_bytes(child)
    public = open_document(native_parent, strict=True, include_brep=False, include_tessellation=False)
    require(public.source.sha256 == digest(parent) and public.assembly.documents[0].document.source.sha256 == digest(child),
            "normal reader did not resolve the actual generated files")
    _, emission["normal_read"] = observe_manager(public, parent, True)
    require(emission["normal_read"]["creation_subservice_pack"] == request[2].TargetValue.SubservicePack,
            "new feature provenance differs from its explicit writer target")
    emission["normal_read"]["lights"] = public_light_rows(public, light_members, lights)
    _, notes = observe(public, parent, 2)
    emission["normal_read"]["annotation_keyword_rows"] = notes["annotation_keyword_rows"]
    require(len(public.feature_timeline) == 25 and public.metadata["solidworks.typed_mates_semantics"]["status"] == "unsupported",
            "generated exploded manager changed the expected inventory or admitted a pre-solve mate")
    failures = refusal_cases(request, raw)
    whole_source = rejected({"whole_source": lambda: ReadAsmModel(source)})
    require(whole_source["whole_source"] == "assembly root contains unprojected model content", "whole-source admission changed")
    flat = verify_legacy(args.prior_source_closure, out)
    nested = nested_regressions(args.prior_source_closure)
    for (_, folder, names, hashes), row in zip(inputs, layouts, strict=True):
        for filename, evidence, role in zip(names, hashes, ("parent", "child"), strict=True):
            checked(folder / filename, evidence)
            row[role + "_sha256"] = evidence
    require(source_inventory(args.prior_source_closure) == before and source_inventory(REPO) == after, "frozen source changed")
    result = {"schema": "kit.sw2026.disclosed-parent-empty-exploded-view.v1", "baseline": BASELINE, "passed": True,
              "source_closures": {"before": inventory_receipt(before), "after": inventory_receipt(after)},
              "changed_sources_sha256": {name: after[name] for name in sorted(delta)}, "disclosed_sources": layouts,
              "disclosed_inputs_unchanged": True, "neutral_document_sha256": json_digest(neutral),
              "emission": emission, "refused": failures, "whole_source_guards": whole_source,
              "previous_flat": flat, "previous_nested": nested, "native_processes": 0, "heldout_inputs_read": 0}
    text = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    (out / "Report.json").write_text(text)
    print(text, end="")


if __name__ == "__main__":
    main()
