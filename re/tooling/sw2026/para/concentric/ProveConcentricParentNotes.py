import argparse
from dataclasses import asdict, replace
import codecs
import json
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[5]
SW2026 = REPO / "re/tooling/sw2026"
sys.path[:0] = [str(REPO), str(REPO / "src"), str(SW2026), str(SW2026 / "serial")]

from CheckConcentricSourceBrep import map_source_endpoints
from convert import open_document
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.solidworks.Archive.Construction.Assembly.MakeAsmBase import MakeAsmBase
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.AsmKeyNodes import AsmKeyNodes
from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import FeatureInstant
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadNodeName, ReadRows, RequireRecord
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import ReadAsmModel
from convert.adapters.solidworks.Core.Native import ParseKeywords
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadNotesInput import ReadNotesInput
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadChildren import ReadChildren
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.serialization.Deserialize import FromData
from para.concentric.ProjectConcentricRadialIntent import read_intents
from para.concentric.ProveConcentricParentLights import EPOCH, ROOT_NAME, SEED, digest, disclose, nested_regressions
from para.concentric.ProveConcentricParentLights import public_light_rows, read_scene, with_lights
from para.concentric.ProveConcentricSourceBrep import D01_LOCKED, RADIAL_LOCKED, checked, json_digest, require, source_case
from para.concentric.ProveSignedConcentricWriter import emit_parts, inventory_receipt, neutral_d01, plan_bundle
from para.concentric.ProveSignedConcentricWriter import source_inventory, verify_legacy, verify_parts


BASELINE = "4cd5aee928b67bc9d3b9c55a33587d2aea338f56"
TOOL = "re/tooling/sw2026/para/concentric/ProveConcentricParentNotes.py"
SCOPE = ("AssemblySysIn.py", "System/MakeAsmSysMut.py", "Xml/AsmKeyNodes.py", "Xml/AsmXmlRoles.py")
CONFIG = "Contents/Config-0"
RESOLVED = CONFIG + "-ResolvedFeatures"
KEYWORDS = "swXmlContents/KeyWords"
LIGHT_ONLY = "94281a87134de185727a914108993acbc8db97401c19e5a18ce1fda9677a32ae"
EMPTY_SYSTEM = "976a38d062e23093f2ad90e63ed781cfffd156ad3391d516295ecd9ce2b29da1"
CHILD = "1f57dc2b626d97a737b8b1dddd1eebd415e30530c018425c1db9cfcec598bab2"


def cabinet_owner(roots):
    cabinets = tuple(row for row in roots if row.ClassValue.NameValue == "moDetailCabinet_c")
    require(len(cabinets) == 1, "source requires one actual resolved annotation cabinet")
    return cabinets[0]


def read_notes(link, count):
    resolved = link.ResolvedValue
    require(link.ConfigName == CONFIG and all(
        row.get("completed") and not row.get("missing_schemas") and not row.get("provisional_schemas")
        for row in (link.ConfigValue.ReportValue, resolved.ReportValue)
    ), "actual configuration and annotation graph must be complete")
    cabinet = cabinet_owner(resolved.RootsValue)
    require(not any(row is cabinet for row in link.ConfigValue.RootValue.FieldsValue.values()),
            "annotation cabinet scope differs from its ordinary resolved-only profile")
    empty = {"n": 0, "items": []}
    require(all(cabinet.FieldsValue.get(field) == value for field, value in {
        "f35c": 0, "f368": empty, "f370": 1.0, "f378": 1.0, "f388": empty, "n3d8": 0, "f3d8": [], "f3f0": 0,
    }.items()), "annotation cabinet has unrepresented contents or presentation")
    fields = RequireRecord(cabinet.FieldsValue.get("f60"))
    listing = RequireRecord(fields.get("list"))
    require(set(fields) == {"list", "tail"} and fields["tail"] == 0 and set(listing) == {"n", "items"}
            and all(set(row) == {"o"} for row in ReadRows(listing["items"])),
            "annotation cabinet contains unsupported list or item state")
    members = ReadChildren(cabinet)
    require(len(members) == count and count in (0, 2), "annotation membership count differs from the selected profile")
    require(all(sum(entry.EntryValue is row for entry in resolved.MapValue.EntriesValue) == 1 for row in (cabinet, *members))
            and not any(member is row for member in members for row in resolved.RootsValue),
            "annotation members must occur once under the actual cabinet without flat resolved duplicates")
    ids = tuple(FieldInt(row.FieldsValue, "f08") for row in (cabinet, *members))
    require(len(set(ids)) == len(ids) and all(value > 0 for value in ids),
            "annotation cabinet and members have conflicting persistent IDs")
    require(all(row.FieldsValue.get("hidden") == 0 for row in members),
            "hidden notes are outside the ordinary disclosed empty pair")
    return cabinet, members, ReadNotesInput(members) if members else None


def check_keywords(document, archive, cabinet, members):
    expected = [(FieldInt(row.FieldsValue, "f08"), ReadNodeName(row), "Annotations" if row is cabinet else "Notes")
                for row in (cabinet, *members)]
    ids = {row[0] for row in expected}
    _, words = ParseKeywords(archive.require(KEYWORDS))
    raw_rows = [row for row in words if row.object_id in ids or row.kind in {"Notes", "Annotations"}]
    public_rows = [row for row in document.feature_timeline
                   if row.attributes.get("native_object_id") in ids or row.attributes.get("native_type") in {"Notes", "Annotations"}]
    expected_rows = {value: {"id": str(value), "Name": name, "Type": kind} for value, name, kind in expected}
    require(len(expected) == len(raw_rows) == len(public_rows)
            and {row.object_id: row.properties for row in raw_rows} == expected_rows
            and all(row.xml_tag == "Feature" and not row.dimensions for row in raw_rows)
            and {row.attributes["native_object_id"]: row.attributes["native_properties"] for row in public_rows} == expected_rows
            and all(row.attributes["xml_tag"] == "Feature" and row.name == row.attributes["native_properties"]["Name"]
                    and row.attributes["native_type"] == row.attributes["native_properties"]["Type"] for row in public_rows),
            "annotation keywords must index each actual cabinet identity once with its exact typed role")
    return expected


def observe(document, raw, count):
    archive = SldprtArchive.from_bytes(raw)
    cabinet, members, intent = read_notes(ReadNativeLink(archive, 0), count)
    rows = check_keywords(document, archive, cabinet, members)
    return intent, {
        "annotation_keyword_rows": rows, "note_intent": asdict(intent) if intent else None,
        "partner_ids": [FieldInt(row.FieldsValue["f388"].FieldsValue, "f08") for row in members],
        "head_markers": [FieldInt(row.FieldsValue, "f37c") for row in members],
        "feature_rows": len(document.feature_timeline), "parent_sdk_model_sha256": json_digest(document),
    }


def with_notes(bundle, cabinet, intent):
    attachment, mate, settings, poses = bundle
    system = replace(settings.SystemValue, CabinetName=cabinet, NotesValue=intent)
    return attachment, mate, replace(settings, SystemValue=system), poses


def rejected(cases):
    result = {}
    for name, action in cases.items():
        try:
            action()
        except (ValueError, TypeError) as error:
            result[name] = str(error)
        else:
            raise ValueError("unsupported annotation case was admitted: " + name)
    return result


def source_refusals(document, raw):
    def changed(target, field, value, index=0):
        archive = SldprtArchive.from_bytes(raw)
        link = ReadNativeLink(archive, 0)
        cabinet = cabinet_owner(link.ResolvedValue.RootsValue)
        owners = {"cabinet": cabinet.FieldsValue, "note": ReadChildren(cabinet)[index].FieldsValue,
                  "owner_list": cabinet.FieldsValue["f60"], "count": cabinet.FieldsValue["f60"]["list"]}
        owners[target][field] = value
        return read_notes(link, 2)

    def missing_keyword():
        archive = SldprtArchive.from_bytes(raw)
        cabinet, members, _ = read_notes(ReadNativeLink(archive, 0), 2)
        member = FieldInt(members[0].FieldsValue, "f08")
        incomplete = replace(document, feature_timeline=tuple(row for row in document.feature_timeline
                                                               if row.attributes.get("native_object_id") != member))
        return check_keywords(incomplete, archive, cabinet, members)

    return rejected({
        "source_annotation_state": lambda: changed("cabinet", "f3f0", 1),
        "source_owner_count": lambda: changed("count", "n", 1),
        "source_owner_list_tail": lambda: changed("owner_list", "tail", 1),
        "source_wrong_partner": lambda: changed("note", "f388", None),
        "source_wrong_head_marker": lambda: changed("note", "f37c", 1, 1),
        "source_nonempty_note_payload": lambda: changed("note", "f370", 1),
        "source_hidden_note": lambda: changed("note", "hidden", 1),
        "source_keyword_without_public_owner": missing_keyword,
    })


def writer_refusals(bundle, caption, notes):
    def changed(scope, field, value):
        state = MakeAsmBase(with_notes(bundle, caption, notes)[2])
        cabinet = cabinet_owner(state.FeatureValues)
        note = ReadChildren(cabinet)[0]
        owner = {"cabinet": cabinet, "note": note}[scope]
        owner.FieldsValue[field] = value(state, note)
        return AsmKeyNodes(state.RootValue, state.FeatureValues)

    def reject_flat(actual):
        state = MakeAsmBase(with_notes(bundle, caption, notes)[2])
        note = ReadChildren(cabinet_owner(state.FeatureValues))[0]
        if not actual:
            note = replace(note, FieldsValue={**note.FieldsValue, "f08": 65000})
        return AsmKeyNodes(state.RootValue, (*state.FeatureValues, note))

    return rejected({
        "untyped_pair": lambda: with_notes(bundle, caption, {"HeadName": "Notes"}),
        "system_caption_collision": lambda: with_notes(bundle, caption, replace(notes, HeadName="Origin")),
        "light_caption_collision": lambda: with_notes(bundle, caption, replace(notes, HeadName=bundle[2].SystemValue.LightValues[0].NameValue)),
        "wrong_end_tag": lambda: with_notes(bundle, caption, replace(notes, EndName="Other")),
        "foreign_cabinet_owner": lambda: changed("cabinet", "owner", lambda _, note: note),
        "foreign_note_owner": lambda: changed("note", "owner", lambda state, _: state.RootValue),
        "unpaired_note": lambda: changed("note", "f388", lambda _, note: note),
        "same_id_as_light": lambda: changed("note", "f08", lambda state, _: FieldInt(
            ReadChildren(state.RootValue.FieldsValue["f1e0"])[0].FieldsValue, "f08")),
        "flat_note_duplicate": lambda: reject_flat(True),
        "flat_note_foreign": lambda: reject_flat(False),
    })


def build(document, axes, light_caption, lights, cabinet_caption, source_notes):
    GetDocumentCaps(ReadAsmModel(document).ChildDocument)
    for encoding in ("utf-16-le", "utf-16-be", "cp1252", "utf-8"):
        codecs.lookup(encoding)
    notes = replace(source_notes, HeadCreated=FeatureInstant(EPOCH + len(lights), 1),
                    EndCreated=FeatureInstant(EPOCH + len(lights), 2))
    contrast_notes = replace(notes, HeadName=notes.HeadName + " Host Discriminator")
    denied = []

    def guard(event, _):
        if enabled and event in {"open", "subprocess.Popen", "os.system", "os.posix_spawn", "os.fork", "socket.connect"}:
            denied.append(event)
            raise RuntimeError("annotation writer attempted runtime access: " + event)

    enabled = True
    sys.addaudithook(guard)
    try:
        bare = plan_bundle(document, EPOCH)
        light_bundle = with_lights(bare, light_caption, lights)
        combined = with_notes(light_bundle, cabinet_caption, notes)
        parent = emit_parts(combined, axes)
        repeated = with_notes(with_lights(plan_bundle(document, EPOCH), light_caption, lights), cabinet_caption, notes)
        require(emit_parts(repeated, axes) == parent and combined[0].file_bytes == repeated[0].file_bytes,
                "independent note construction did not repeat exactly")
        note_archive = SldprtArchive.from_bytes(parent)
        note_link = ReadNativeLink(note_archive, 0)
        cabinet, nodes, output_notes = read_notes(note_link, 2)
        require(output_notes == notes and ReadNodeName(cabinet) == cabinet_caption, "generated annotation intent differs")
        ids = [FieldInt(row.FieldsValue, "f08") for row in nodes]
        require(all(ident < FieldInt(note_link.ConfigValue.HeaderValue.FieldsValue, "f08") for ident in ids),
                "annotation IDs must share the published assembly allocator")
        _, light_nodes, observed_lights = read_scene(note_link)
        require(observed_lights == lights, "note publication changed the actual environment members")
        bare_bytes = emit_parts(bare, axes)
        light_bytes = emit_parts(light_bundle, axes)
        require(digest(bare_bytes) == EMPTY_SYSTEM and digest(light_bytes) == LIGHT_ONLY
                and digest(combined[0].file_bytes) == CHILD, "previous guarded absent-note files changed")
        empty_note_archive = SldprtArchive.from_bytes(light_bytes)
        read_notes(ReadNativeLink(empty_note_archive, 0), 0)
        contrast = SldprtArchive.from_bytes(emit_parts(with_notes(light_bundle, cabinet_caption, contrast_notes), axes))
        require(read_notes(ReadNativeLink(contrast, 0), 2)[2] == contrast_notes, "edited annotation label did not survive")
        sizes = {name: len(arc.require(RESOLVED)) for name, arc in
                 (("absent", empty_note_archive), ("notes", note_archive), ("longer_head", contrast))}
        require(sizes["absent"] < sizes["notes"] < sizes["longer_head"],
                "generated resolved stream size did not follow note content")
        alone = SldprtArchive.from_bytes(emit_parts(with_notes(bare, cabinet_caption, notes), axes))
        alone_link = ReadNativeLink(alone, 0)
        require(read_notes(alone_link, 2)[2] == notes, "note-only assembly did not retain its intent")
        read_scene(alone_link, empty=True)
        failures = writer_refusals(light_bundle, cabinet_caption, notes)
        mate_proof = verify_parts(parent, combined, axes)
    finally:
        enabled = False
    require(not denied, "annotation construction used implicit runtime inputs")
    return parent, combined[0].file_bytes, light_nodes, {
        "parent_sha256": digest(parent), "child_sha256": digest(combined[0].file_bytes),
        "light_only_parent_sha256": digest(light_bytes), "empty_system_parent_sha256": digest(bare_bytes),
        "resolved_stream_bytes": sizes, "changed_streams": sorted(
            key for key in note_archive.streams if note_archive.require(key) != empty_note_archive.require(key)),
        "binary_mate_and_linked_streams": mate_proof, "note_only_without_lights": True,
        "guarded_repeats": 2, "runtime_file_process_network_attempts": len(denied),
        "writer_refusals": failures, "writer_note_intent": asdict(notes),
    }


def main():
    parser = argparse.ArgumentParser(description="Prove the disclosed concentric parent empty annotation pair")
    parser.add_argument("disclosed_root", type=Path)
    parser.add_argument("prior_source_closure", type=Path)
    parser.add_argument("new_scratch", type=Path)
    args = parser.parse_args()
    before = source_inventory(args.prior_source_closure)
    after = source_inventory(REPO)
    deltas = {name for name in set(before) | set(after) if before.get(name) != after.get(name)}
    prefix = "src/convert/adapters/solidworks/Archive/Construction/Assembly/"
    require(deltas == {TOOL, *(prefix + path for path in SCOPE)}, "proof code differs from the exact scoped overlay")
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
    original, result = observe(source, raw, 2)
    disclosure_rows = [{"case": inputs[0][0], **result}]
    for label, folder, names, hashes in inputs[1:]:
        item, payload, _ = source_case(folder, *names, hashes)
        intent, result = observe(item, payload, 0 if label == "RadialFrozen" else 2)
        if label == "D01Edited":
            require(intent == original, "D01 real depth edit changed annotation intent")
        if label == "RadialSaved":
            require((intent.HeadName, intent.EndName) == (original.HeadName, original.EndName)
                    and intent.HeadCreated != original.HeadCreated, "radial native-save control lacked an independent annotation pair")
        disclosure_rows.append({"case": label, **result})
    axes_owner = map_source_endpoints(source, raw, shape, shape)
    axes = tuple(row["local_axis"] for row in axes_owner)
    seed = FromData(json.loads(checked(REPO / "re/solidworks/inputs/ConcentricFeatureNeutral01.json", SEED)))
    neutral = neutral_d01(seed, source, axes_owner, shape, ROOT_NAME)
    cabinet_caption = disclosure_rows[0]["annotation_keyword_rows"][0][1]
    lights = read_intents(light_intents, EPOCH)
    parent, child, light_nodes, emission = build(neutral, axes, light_caption, lights, cabinet_caption, original)
    out = args.new_scratch.resolve()
    out.mkdir()
    new_parent = out / (ROOT_NAME + ".SLDASM")
    new_parent.write_bytes(parent)
    (out / "D01SignedChild.SLDPRT").write_bytes(child)
    public = open_document(new_parent, strict=True, include_brep=False, include_tessellation=False)
    require(public.source.sha256 == digest(parent) and public.assembly.documents[0].document.source.sha256 == digest(child),
            "normal reader did not resolve the actual generated parent and child")
    _, emission["normal_read"] = observe(public, parent, 2)
    emission["normal_read"]["light_keyword_rows"] = public_light_rows(public, light_nodes, lights)
    require(len(public.feature_timeline) == 24 and public.metadata["solidworks.typed_mates_semantics"]["status"] == "unsupported",
            "the generated parent has the wrong inventory or admitted a pre-solve mate")
    guard = rejected({"whole_source": lambda: ReadAsmModel(source)})
    require(guard["whole_source"] == "assembly root contains unprojected model content", "whole-source admission changed")
    flat = verify_legacy(args.prior_source_closure, out)
    nested = nested_regressions(args.prior_source_closure)
    for (_, folder, names, hashes), row in zip(inputs, disclosure_rows, strict=True):
        for filename, evidence, role in zip(names, hashes, ("parent", "child"), strict=True):
            checked(folder / filename, evidence)
            row[role + "_sha256"] = evidence
    require(json_digest(source) == disclosure_rows[0]["parent_sdk_model_sha256"], "disclosed model changed during transfer")
    require(source_inventory(args.prior_source_closure) == before and source_inventory(REPO) == after, "frozen source changed")
    report = {
        "schema": "kit.sw2026.disclosed-parent-note-projection.v1", "baseline": BASELINE, "passed": True,
        "source_closures": {"before": inventory_receipt(before), "after": inventory_receipt(after)},
        "changed_sources_sha256": {name: after[name] for name in sorted(deltas)}, "disclosed_sources": disclosure_rows,
        "disclosed_inputs_unchanged": True, "emission": emission, "neutral_document_sha256": json_digest(neutral),
        "source_refusals": source_refusals(source, raw), "whole_source_guards": guard,
        "previous_flat": flat, "previous_nested": nested, "native_processes": 0, "heldout_inputs_read": 0,
    }
    receipt = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    (out / "Report.json").write_text(receipt)
    print(receipt, end="")


if __name__ == "__main__":
    main()
