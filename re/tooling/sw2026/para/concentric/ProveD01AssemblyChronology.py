from argparse import ArgumentParser
from copy import deepcopy
from dataclasses import asdict, dataclass, replace
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace


HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from ProveD01RootHistory import FILES, REPO, VISUAL, build, inputs, relocate_visual, verify_owned_edit
from ProveD01ConcentricBridge import fingerprint, proof_guard
from CheckConcentricAssembly import verify_emission
from ProveConcentricCmgrHistory import apply_history, refuse, selection_plan, verify_current
from ProveConcentricSourceBrep import D01_LOCKED, checked, source_case
from ProveD01ChildAppearance import wire
from ProveD01ParentDisplay import build_arguments
from ProjectConcentricRadialIntent import read_intents
from PlanarRendererInput import from_json
from ProjectD01Concentric import project_d01, require
from ReadConcentricCmgrInputs import owned_source
from ReadD01RootHistory import HEADER, MATES, TOP
from ProveVisualStateStore import owner_clocks, replay
from MakeVisualStateStore import make_visual_store
from D01RevisionIntent import (
    EXPLODED, MODEL, attach_intent, clocks, header_seed, make_book, make_instants, ordered_occurrences,
    owners, read_book, read_instants, revision_fields,
)
from para.concentric.MakeDisplayTree import DisplayListIntent, DisplayStateIntent
from Classes import registry

from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import AssemblyState
from convert.adapters.solidworks.Archive.Construction.Assembly.CheckAsmMeta import CheckAsmMeta
from convert.adapters.solidworks.Archive.Construction.Assembly.EmitAsmStreams import EmitAsmStreams
from convert.adapters.solidworks.Archive.Construction.Assembly.Headers.MakeAsmHeaders import MakeAsmHeaders
from convert.adapters.solidworks.Archive.Construction.Assembly.MakeAsmBase import MakeAsmBase
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.PutPartRefsMut import PutPartRefsMut
from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.CheckGroupChild import CheckGroupChild
from convert.adapters.solidworks.Archive.Construction.Circles.RadialLabelIn import RadialLabelIn
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CheckCylNames import CheckCylNames
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CylMateCtx import CylMateCtx
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.MakeCylMateMut import MakeCylMateMut
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import PartCandidate
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.AssemblyPreparation.Concentric.PlanCylMate import PlanCylMate
from convert.adapters.solidworks.Core.AssemblyPreparation.Concentric.PrepCylChild import PrepCylChild
from convert.adapters.solidworks.Core.AssemblyPreparation.Concentric.ReadConcMate import ReadConcMate
from convert.adapters.solidworks.Core.AssemblyPreparation.Paths.ReadAsmPaths import ReadAsmPaths
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.serialization.Deserialize import FromData


BASE = "4f3fe8ee989b7df7b15c9b87c29793617047e1aa"
PRIOR = "9be4fcf109235e41b0d240d3bb1e0c929cb67235047065000c3242e9b6c945c9"
RESOLVED = "Contents/Config-0-ResolvedFeatures"
HISTORY = "_MO_VERSION_19000/History"
BIOGRAPHY = "_MO_VERSION_19000/Biography"
DIFFERENTIAL = {HEADER, TOP, VISUAL}


@dataclass(frozen=True)
class ParentRoots:
    StateValue: AssemblyState
    ChildValue: PartCandidate
    OccurrenceValues: tuple[ArchiveNode, ...]
    MateValues: tuple[ArchiveNode, ...]
    HeaderValue: ArchiveNode
    TopHeader: ArchiveNode
    StreamsValue: dict[str, bytes]
    FaceTag: int


def archive_roles(archive):
    link = ReadNativeLink(archive, 0)
    root = link.ConfigValue.RootValue
    mate_graph = ReadMatesMut(archive.require(MATES), link.ResolvedValue)
    nodes = owners(root, link.ResolvedValue.RootsValue, ordered_occurrences(root), mate_graph.RootsValue)
    return (link.ConfigValue.HeaderValue, ReadHeaderGraph(archive.require(TOP), 19000)), nodes


def read_headers(archive, headers, nodes):
    first_clock, second_clock = (clocks(header) for header in headers)
    first_book, second_book = (read_book(header, nodes) for header in headers)
    self_nodes = tuple(header.FieldsValue["f38"] for header in headers)
    require(first_clock == second_clock and first_book == second_book
            and all(file.FieldsValue["shared"]["f28"] == first_clock.CreatedAt for file in self_nodes)
            and self_nodes[0].FieldsValue["f60"] == self_nodes[1].FieldsValue["f60"],
            "paired assembly headers disagree on semantic revisions or actual creation/save ownership")
    for key, header in zip((HEADER, TOP), headers, strict=True):
        original = archive.require(key)
        generated = ArchiveNode(header.ClassValue, dict(header.FieldsValue) | revision_fields(make_book(nodes, first_book)))
        require(WriteHeadGraph(header, 19000) == WriteHeadGraph(generated, 19000) == original,
                "typed assembly revision reconstruction differs from the original header: " + key)
    feature_rows = read_instants(nodes)
    require(all(all(node.FieldsValue[key] == value for key, value in fields.items())
                for node, fields in make_instants(nodes, feature_rows)),
            "precise semantic feature moments could not reproduce their own read time words")
    return {"header": asdict(first_clock), "book": first_book, "features": feature_rows}


def inventory(archive, headers, nodes, intent):
    receipts = {}
    for key, header in zip((HEADER, TOP), headers, strict=True):
        fields = header.FieldsValue
        data = archive.require(key)
        receipts[key] = {"bytes": len(data), "sha256": fingerprint(data), "exact_log_reconstruction": True,
                         "model_present": fields["fec"], "next_id": fields["f08"],
                         "update_counter": fields["f40"], "body_counter": fields["f44"],
                         "own_save_seconds": fields["f38"].FieldsValue["f60"]}
    revision_book = intent["book"]
    return {
        "headers": receipts,
        "clocks": intent["header"],
        "chronology_sha256": fingerprint(wire(intent)),
        "attribution_counts": [len(revision_book[key]) for key in ("users", "companies")],
        "revision_owner_ids_in_order": [FieldInt(nodes[row["role"]].FieldsValue, "f08") for row in revision_book["logs"]],
        "root_log_caption": revision_book["logs"][0]["caption"],
        "log_event_counts": [len(row["events"]) for row in revision_book["logs"]],
        "events": sum(len(row["events"]) for row in revision_book["logs"]),
        "clock_owners": [{**row, "owner_id": FieldInt(nodes[row["role"]].FieldsValue, "f08")} for row in intent["features"]],
        "exploded_has_log": any(row["role"] == EXPLODED for row in revision_book["logs"]),
        "stream_count": len(archive.streams),
        "source_runtime_history": {key: {"bytes": len(archive.require(key)), "sha256": fingerprint(archive.require(key))}
                                   for key in (HISTORY, BIOGRAPHY)},
    }


def disclose(disclosures, reg):
    previous_report, transition, models = inputs(disclosures)
    directory = disclosures / "ConcentricMateSourcePacket02/Disclosed/D01/Native"
    intents, summaries, selections = {}, {}, []
    for (name, pins), phase in zip(D01_LOCKED.items(), ("before", "after"), strict=True):
        case_dir = directory / name
        document, raw, shape = source_case(case_dir, *FILES, pins)
        pair = (SldprtArchive.from_bytes(raw),
                SldprtArchive.from_bytes(checked(case_dir / FILES[1], pins[1])))
        projected = project_d01(document, raw, shape)
        selection, _ = owned_source(document, *pair, pins[1], reg, dict(projected.identities["occurrences"]))
        selections.append(selection)
        parent = pair[0]
        headers, nodes = archive_roles(parent)
        intent = read_headers(parent, headers, nodes)
        summary = inventory(parent, headers, nodes, intent)
        visual, _ = replay(parent, reg)
        _, planes = owner_clocks(parent, visual)
        require(planes == previous_report[phase]["plane_clocks"], "source plane references shifted from earlier proof")
        intents[phase] = intent
        summaries[phase] = {**summary, "owner_plane_clocks": planes, "file_sha256": pins[0],
                            "strict_source_refusal": previous_report[phase]["refusals"]["original"],
                            "root_geometry_stamp": nodes[MODEL].FieldsValue["f1300"],
                            "original_streams": sorted(parent.streams)}
    old, new = (intents[key] for key in ("before", "after"))
    require(selections[0] == selections[1] and old["book"] == new["book"] and old["features"] == new["features"]
            and old["header"]["CreatedAt"] == new["header"]["CreatedAt"]
            and old["header"]["ArchiveAt"] == new["header"]["ArchiveAt"]
            and new["header"]["UpdatedAt"] > old["header"]["UpdatedAt"],
            "D01 disclosure does not have a stable original creation history and one subsequent update")
    models["selected_child_views"] = selections[1]
    return {"models": models, "chronology": intents}, summaries, transition


def build_intent(request, document, model, intent):
    epoch = request["written_at"]
    path = ReadAsmPaths(model.RootValue.name, model.ChildValue.name, request["destination"], epoch)
    _, recipe, *_, base_mate = build_arguments(request, document, model)
    CheckAsmMeta(recipe)
    header_recipe = replace(recipe, HeaderValue=header_seed(intent, epoch))
    label = RadialLabelIn(**(request["radial_label"] | {"TextPoint": tuple(request["radial_label"]["TextPoint"])}))
    child = PrepCylChild(model.ChildDocument, path.ChildValue, request["child_scene"],
                         read_intents(request["child_lights"], epoch), LabelValue=label,
                         LookValue=from_json(request["appearance"]))
    plan = PlanCylMate(document, model.ChildDocument, child.CandidateValue, child.FaceTag)
    mate_intent = replace(plan.MateInput, LocalAxes=base_mate.LocalAxes)
    CheckGroupChild(child.CandidateValue, recipe)
    CheckCylNames(recipe, plan.Placements, mate_intent)
    state = MakeAsmBase(recipe)
    headers = MakeAsmHeaders(state, header_recipe)
    refs = PutPartRefsMut(state, child.CandidateValue, recipe, plan.Placements, headers)
    first, second = plan.EndIndexes
    mate = MakeCylMateMut(CylMateCtx(state, recipe, child.CandidateValue, headers),
                          (refs[first], refs[second]), (plan.Placements[first].FrameValue, plan.Placements[second].FrameValue),
                          child.FaceTag, mate_intent)
    return ParentRoots(state, child.CandidateValue, refs, (mate,), *headers, {}, child.FaceTag), recipe


def visual_input(bundle, document, request, reg):
    config_key = FieldInt(bundle.StateValue.CurrentConfig.FieldsValue, "f08")
    refs = tuple(FieldInt(row.FieldsValue, "f08") for row in bundle.OccurrenceValues)
    visible = tuple(not row.hidden for row in document.Occurrences)
    state = DisplayStateIntent(request["root_display_name"], tuple(zip(refs, visible, strict=True)))
    data = make_visual_store(bundle.StateValue, (bundle.HeaderValue, bundle.TopHeader),
                             bundle.OccurrenceValues, DisplayListIntent(config_key, (state,)), reg)
    return replace(bundle, StreamsValue=bundle.StreamsValue | {VISUAL: data})


def compose_streams(request, intents, docs, models, reg, *, refusals=None):
    phases = ("before", "after")
    if intents is None:
        bundles = tuple(build(request[key], doc, model) for key, doc, model in zip(phases, docs, models, strict=True))
        current_recipe = build_arguments(request["after"], docs[1], models[1])[1]
    else:
        built = tuple(build_intent(request[key], doc, model, intents[key])
                      for key, doc, model in zip(phases, docs, models, strict=True))
        bundles = tuple(bundle for bundle, _ in built)
        current_recipe = built[1][1]
        for bundle, key in zip(bundles, phases, strict=True):
            attach_intent(bundle, intents[key])
        bundles = tuple(visual_input(bundle, model, request[key], reg)
                        for bundle, model, key in zip(bundles, models, phases, strict=True))
    previous, current = bundles
    roles = current.StateValue, current.ChildValue, current_recipe, (current.HeaderValue, current.TopHeader)
    selected = selection_plan(current, models[1], request["selected_child_views"], reg)
    if refusals is not None:
        prove_refusals(refusals, previous, current, models, intents, request, reg)
    visual_bytes = relocate_visual(previous, current, models, reg)
    apply_history(previous, current, models, selected)
    streams = EmitAsmStreams(*roles, current.OccurrenceValues, current.MateValues).StreamsValue
    return streams | {VISUAL: visual_bytes}, current


def compose(request, intents, docs, models, reg, *, refusals=None):
    streams, current = compose_streams(request, intents, docs, models, reg, refusals=refusals)
    return BuildSldprt(streams, FormatVersion=4), current


def prove_refusals(result, previous, current, models, intents, request, reg):
    nodes = owners(current.StateValue.RootValue, current.StateValue.FeatureValues,
                   current.OccurrenceValues, current.MateValues, constructed=True)
    current_intent = intents["after"]
    book = current_intent["book"]
    duplicate = book | {"logs": [*book["logs"][:-1], book["logs"][0]]}
    short = book | {"logs": book["logs"][:-1]}
    result["duplicate_log_owner"] = refuse(lambda: make_book(nodes, duplicate), "missing, foreign or duplicated")
    result["omitted_log_owner"] = refuse(lambda: make_book(nodes, short), "inventory omits an actual owner")
    image = current_intent["features"]
    owner = image[-1]
    wrong = [*image[:-1], owner | {"role": MODEL}]
    fraction = [*image[:-1], owner | {"instant": owner["instant"] | {"FractionTicks": 10_000_000}}]
    result["document_is_not_a_feature"] = refuse(lambda: make_instants(nodes, wrong), "missing, foreign or duplicated")
    result["incorrect_tick_range"] = refuse(lambda: make_instants(nodes, fraction), "fractional filetime ticks")
    header = current.TopHeader.FieldsValue
    actual_logs = header["f20"]
    result["divergent_plane_header"] = refuse(
        lambda: unpaired_plane(previous, current, models, nodes, book, reg),
        "plane creation-log owners differ",
    )
    require(header["f20"] is actual_logs, "rejected independent header mutation was not restored")
    copy = [dict(row) for row in request["selected_child_views"]]
    copy[0]["display_name"] = "unbound child state"
    result["invalid_child_state"] = refuse(lambda: selection_plan(current, models[1], copy, reg),
                                          "actual ordered occurrence")


def unpaired_plane(previous, current, models, nodes, book, reg):
    fields = current.TopHeader.FieldsValue
    original = fields["f20"]
    changed, _ = shift_one_plane(book)
    fields["f20"] = revision_fields(make_book(nodes, changed))["f20"]
    try:
        relocate_visual(previous, current, models, reg)
    finally:
        fields["f20"] = original


def shift_one_plane(book):
    changed = deepcopy(book)
    top, = (row for row in changed["logs"] if tuple(row["role"]) == ("resolved", "moRefPlane_c", "Top Plane"))
    top["events"][0]["EventAt"] -= 7
    return changed, top["events"][0]["EventAt"]


def stream_diff(left, right):
    return {key for key in left.streams.keys() | right.streams.keys() if left.streams.get(key) != right.streams.get(key)}


def mate_readback(payload, bundle, model, request):
    child = bundle.ChildValue
    atom, = child.SystemValue.RootValue.FieldsValue["fd88"]["atoms"]
    _, first, second, alignment, locked = ReadConcMate(model)
    names = {row.id: row.name for row in model.Occurrences}
    bridge = SimpleNamespace(candidate=child, atom_id=atom["o"].FieldsValue["f140"],
                             projection=SimpleNamespace(lateral_face_tag=bundle.FaceTag))
    return verify_emission(
        payload, bridge, alignment, locked, model.FixedIndex,
        tuple(names[entity.instance_path[0]] for entity in (first, second)),
        expected_local_axes=tuple(tuple(row) for row in request["endpoint_local_axes"]),
    )


def observe(payload, model, expected, historical_title, reg):
    archive = SldprtArchive.from_bytes(payload)
    headers, nodes = archive_roles(archive)
    actual = read_headers(archive, headers, nodes)
    require(wire(actual) == wire(expected), "generated chronology changed authored captions, event order or precise instants")
    contexts, _, manager = verify_current(model, payload, historical_title, reg)
    visual, visual_summary = replay(archive, reg)
    _, planes = owner_clocks(archive, visual)
    require(all(row["log_event_counts"] == [2, 2] for row in planes),
            "visual plane keys must bind to complete and independent log pairs")
    return {"parent_sha256": fingerprint(payload), "parent_bytes": len(payload),
            "child_sha256": fingerprint(model.ChildValue.BytesValue),
            "parent_chronology": inventory(archive, headers, nodes, actual),
            "visual_roundtrip": visual_summary, "plane_keys": planes,
            "linked_occurrences": contexts, "manager_stamps": manager}


def worker(payload, baseline_digest):
    require(set(payload) == {"models", "chronology"}, "chronology worker accepts only model and history intent")
    request, chronology = payload["models"], payload["chronology"]
    require(set(chronology) == {"before", "after"}, "chronology requires the two actual owned assembly states")
    docs = tuple(FromData(request[key]["document"]) for key in ("before", "after"))
    for doc in docs:
        doc.assert_valid()
    reg = registry()
    audit = proof_guard()
    models = verify_owned_edit(*docs)
    baseline, baseline_bundle = compose(request, None, docs, models, reg)
    require(fingerprint(baseline) == baseline_digest, "previous exact saved-context control changed")
    refusals = {}
    current, current_bundle = compose(request, chronology, docs, models, reg, refusals=refusals)
    previous_title = request["before"]["root_model_name"]
    output = observe(current, current_bundle, chronology["after"], previous_title, reg)
    mate = mate_readback(current, current_bundle, models[1], request["after"])
    edited = deepcopy(chronology)
    edited["after"]["book"], varied_time = shift_one_plane(chronology["after"]["book"])
    contrast, contrast_bundle = compose(request, edited, docs, models, reg)
    varied = observe(contrast, contrast_bundle, edited["after"], previous_title, reg)
    require(mate_readback(contrast, contrast_bundle, models[1], request["after"]) == mate,
            "independent plane revision event unexpectedly changed the actual signed concentric mate")
    baseline_archive, archive, variant = map(SldprtArchive.from_bytes, (baseline, current, contrast))
    source_changes = stream_diff(baseline_archive, archive)
    contrast_changes = stream_diff(archive, variant)
    require(source_changes >= {HEADER, TOP, MATES, RESOLVED, VISUAL}
            and not source_changes & {HISTORY, BIOGRAPHY, "Contents/Definition"}
            and contrast_changes == DIFFERENTIAL
            and current_bundle.ChildValue.BytesValue == baseline_bundle.ChildValue.BytesValue
            == contrast_bundle.ChildValue.BytesValue,
            "independent log edit changed geometry, feature clocks, child or unrelated archive streams")
    before, after = output["plane_keys"], varied["plane_keys"]
    delta = [(one, two) for one, two in zip(before, after, strict=True) if one != two]
    require(len(delta) == 1 and delta[0][1]["visual_seconds"] == varied_time
            and delta[0][1]["resolved_filetime_seconds"] == delta[0][0]["resolved_filetime_seconds"]
            and not audit, "the moved creation log did not bind to exactly one real same-FILETIME plane")
    return {"base_parent_sha256": fingerprint(baseline), "original_chronology": output,
            "altered_one_plane_event": {key: varied[key] for key in ("parent_sha256", "parent_bytes", "visual_roundtrip")},
            "differential_plane": delta[0], "actual_mate": mate,
            "modeled_changes": sorted(source_changes), "one_log_only_changes": sorted(contrast_changes),
            "parent_stream_count": len(archive.streams), "child_unchanged": True,
            "runtime_accesses": len(audit), "refusals": refusals, "generated_streams": sorted(archive.streams)}


def main():
    parser = ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--worker")
    mode.add_argument("--disclosures", type=Path)
    args = parser.parse_args()
    if args.worker:
        sys.stdout.buffer.write(wire(worker(json.load(sys.stdin), args.worker)))
        return
    prior_path = REPO / "re/solidworks/measurements/2026/ConcentricSavedCmgrModel01.json"
    prior = json.loads(checked(prior_path, PRIOR))
    request, source_ledger, transition = disclose(args.disclosures, registry())
    data = wire(request)
    command = (sys.executable, "-I", "-B", str(HERE), "--worker", prior["generated"]["parent_sha256"])
    first, second = (subprocess.run(command, input=data, capture_output=True, timeout=180) for _ in range(2))
    require(first.returncode == second.returncode == 0 and first.stdout == second.stdout,
            (first.stderr + second.stderr).decode() or "independent modeled chronology workers disagree")
    generated = json.loads(first.stdout)
    generated["unrepresented_original_streams"] = sorted(
        set(source_ledger["after"]["original_streams"]) - set(generated["generated_streams"])
    )
    output = {
        "schema": "kit.sw2026.d01-assembly-chronology.v1", "base": BASE,
        "prior_saved_context_receipt_sha256": PRIOR, "source_transition": transition,
        "disclosed_sources": source_ledger, "neutral_request_sha256": fingerprint(data),
        "generated": generated, "guarded_writer_processes": 2,
        "native_runs": 0, "heldout_reads": 0, "whole_source_admitted": False, "public_publication": False,
        "source_sha256": {str(path.relative_to(REPO)): fingerprint(path.read_bytes())
                          for path in (HERE, HERE.with_name("D01RevisionIntent.py"))},
    }
    print(json.dumps(output, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
