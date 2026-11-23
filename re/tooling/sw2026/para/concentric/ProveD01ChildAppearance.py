from argparse import ArgumentParser
from base64 import b64decode, b64encode
from dataclasses import asdict, replace
import json
from pathlib import Path, PureWindowsPath
import subprocess
import sys
from types import SimpleNamespace


HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from ProveD01RadialLabel import owned_label
from ProveD01ParentDisplay import build_arguments, source_store
from ProveD01ConcentricBridge import (
    AUTHOR, FILES, LOCK, REPO, VISUAL, compare_root, fingerprint, model_request,
    proof_guard, reversible_child, role_document,
)

sys.path.insert(0, str(REPO / "re/tooling/sw2026/planar_registry"))

from PlanarRendererInput import confirm_look, from_json, request_look
from PlanarVisualOwners import child_store, parent_store, source_definition
from AuditConcentricDisplayState import compare_typed
from Classes import registry
from CheckConcentricAssembly import verify_emission
from ProjectConcentricRadialIntent import read_intents
from ProjectD01Concentric import project_d01, require
from ProveConcentricSourceBrep import D01_LOCKED, checked, source_case
from ProveVisualStateStore import replay

from convert.adapters.solidworks.Archive.Construction.Assembly.Displays.AsmDisplayIn import AsmDisplayIn
from convert.adapters.solidworks.Archive.Construction.Circles.RadialLabelIn import RadialLabelIn
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.MakeCylAsm import MakeCylAsm
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.BasicPbrInput import BasicPbrInput
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.ClassicLook import ClassicLook
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.AssemblyPreparation.Concentric.PlanCylMate import PlanCylMate
from convert.adapters.solidworks.Core.AssemblyPreparation.Concentric.PrepCylAsm import PrepCylAsm
from convert.adapters.solidworks.Core.AssemblyPreparation.Concentric.PrepCylChild import PrepCylChild
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import ReadAsmModel
from convert.adapters.solidworks.Core.AssemblyPreparation.Paths.ReadAsmPaths import ReadAsmPaths
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.serialization.Deserialize import FromData


BASE = "ffa49a63caf2b3c433c05433c7b638e5d0d4fde7"
EPOCH = 1816327100
DISPLAY_AUDIT = "6d2e2dcddbaf2db31696cd925e0d8e360947ee29db739a8b7a1cdb9c0c98c944"
DEFINITION = "Contents/Definition"
CMGR = "Contents/CMgr"
CONFIG = "Contents/Config-0"


def wire(value):
    return json.dumps(value, sort_keys=True, allow_nan=False).encode()


def refused(call, part):
    try:
        call()
    except (ValueError, TypeError) as error:
        require(part in str(error), "unexpected refusal: " + str(error))
        return str(error)
    raise ValueError("unqualified child appearance reached emission")


def emitted(parent, plan, child):
    atom, = child.SystemValue.RootValue.FieldsValue["fd88"]["atoms"]
    bridge = SimpleNamespace(candidate=child, atom_id=atom["o"].FieldsValue["f140"],
                             projection=SimpleNamespace(lateral_face_tag=plan.FaceValue.FaceTag))
    return verify_emission(
        parent.BytesValue, bridge, plan.MateInput.AlignmentCode, False, plan.ModelValue.FixedIndex,
        tuple(plan.ModelValue.Occurrences[index].name for index in plan.EndIndexes),
        expected_local_axes=plan.MateInput.LocalAxes)


def owner_refusals(arguments, child, comparison_child, one_state):
    def compose(value=child, states=one_state):
        return MakeCylAsm(value, *arguments, DisplayValues=states)

    results = {
        "unowned_store": refused(lambda: compose(replace(child, SelfView=None)),
                                 "ordinary radial child without a visual store"),
        "mixed_states": refused(lambda: compose(states=(*one_state, replace(one_state[0], NameValue="Mixed"))),
                                "requires its named look and singleton parent state"),
    }
    for name, changes, reason in (
        ("missing_store", {VISUAL: None}, "visual store does not match its model owners"),
        ("foreign_definition", {DEFINITION: comparison_child.StreamsValue[DEFINITION]},
         "appearance Definition disagrees with its graph"),
    ):
        streams = dict(child.StreamsValue)
        for key, value in changes.items():
            if value is None:
                del streams[key]
            else:
                streams[key] = value
        changed = replace(child, StreamsValue=streams, BytesValue=BuildSldprt(streams, FormatVersion=4))
        results[name] = refused(lambda: compose(changed), reason)

    managers = child.DefinitionValue.DocumentValue.FieldsValue["f1110"]
    managers["f08"] += 1
    try:
        results["crossed_allocator"] = refused(compose, "actual independent appearance allocator")
    finally:
        managers["f08"] -= 1
    model = child.SystemValue.RootValue.FieldsValue["f78"]
    config = child.CurrentConfig.FieldsValue["f78"]
    separate = config.FieldsValue["f88"]
    config.FieldsValue["f88"] = model.FieldsValue["f88"]
    try:
        results["aliased_renderer"] = refused(compose, "lost the actual live renderer owners")
    finally:
        config.FieldsValue["f88"] = separate
    return results


def worker(request):
    document = FromData(request["document"])
    model = ReadAsmModel(document)
    label = request["radial_label"]
    label = RadialLabelIn(label["SketchId"], label["ParameterId"], tuple(label["TextPoint"]))
    look = from_json(request["appearance"])
    time, path = request["written_at"], request["destination"]
    paths = ReadAsmPaths(model.RootValue.name, model.ChildValue.name, path, time)
    lights = read_intents(request["child_lights"], time)
    state = (AsmDisplayIn(request["root_display_name"],
                          tuple((row.name, not row.hidden) for row in model.Occurrences)),)
    reg = registry()
    audit = proof_guard()
    bare_arguments = build_arguments(request, document, model)
    bare = MakeCylAsm(*bare_arguments, DisplayValues=state)

    def compose(label_value, look_value):
        attached = PrepCylChild(model.ChildDocument, paths.ChildValue, request["child_scene"],
                                lights, LabelValue=label_value, LookValue=look_value)
        plan = PlanCylMate(document, model.ChildDocument, attached.CandidateValue, attached.FaceTag)
        plan = replace(plan, MateInput=replace(plan.MateInput, LocalAxes=bare_arguments[-1].LocalAxes))
        args = (bare_arguments[1], plan.Placements, plan.EndIndexes, attached.FaceTag, plan.MateInput)
        return MakeCylAsm(attached.CandidateValue, *args, DisplayValues=state), plan, args

    labels, _, _ = compose(label, None)
    finished, plan, args = compose(label, look)
    ordinary = PrepCylAsm(document, path, time, request["child_scene"], lights,
                          DisplayValues=state, LabelValue=label, LookValue=look)
    child = finished.ChildValue
    require(ordinary.ChildValue.BytesValue == child.BytesValue
            and bare.BytesValue == labels.BytesValue == finished.BytesValue,
            "renderer or label changed actual parent bytes or the internal child route")
    before, after = labels.ChildValue.StreamsValue, child.StreamsValue
    changes = {key for key in before.keys() | after.keys() if before.get(key) != after.get(key)}
    require(changes == {CMGR, CONFIG, DEFINITION, VISUAL},
            "unexpected child renderer stream delta: " + repr(sorted(changes)))
    require(owned_label(ReadNativeLink(SldprtArchive.from_bytes(labels.ChildValue.BytesValue), 0))
            == owned_label(ReadNativeLink(SldprtArchive.from_bytes(child.BytesValue), 0)),
            "renderer modified an actual radial display or driver")
    negatives = owner_refusals(args, child, labels.ChildValue, state)
    for name, bad, match in (
        ("foreign_resource", replace(look, ResourceName=r"graphics\materials\unrepresented.p2m"),
         "explicit ordinary stock color resource"),
        ("exhausted_allocator", replace(look, StartAppearanceId=(1 << 64) - 2),
         "two nonwrapping appearance allocation events"),
    ):
        negatives[name] = refused(lambda: compose(label, bad), match)
    archive = SldprtArchive.from_bytes(child.BytesValue)
    appearance = confirm_look(archive, reg, request["appearance"])
    child_roles = child_store(archive, reg, rich=True)
    parent_roles = parent_store(SldprtArchive.from_bytes(finished.BytesValue), reg)
    require(not appearance["provisional_schemas"] and not child_roles["provisional_schemas"]
            and not parent_roles["provisional_schemas"] and not audit,
            "guarded appearance report contains external accesses or provisional classes")
    return {
        "parent": b64encode(finished.BytesValue).decode(),
        "child": b64encode(child.BytesValue).decode(),
        "unchanged_parent_streams": len(finished.StreamsValue),
        "unchanged_child_streams": len(before) - len(changes & before.keys()),
        "child_changed_streams": sorted(changes),
        "plain_child_sha256": fingerprint(bare.ChildValue.BytesValue),
        "label_child_sha256": fingerprint(labels.ChildValue.BytesValue),
        "appearance": appearance, "child_store": child_roles, "parent_store": parent_roles,
        "mate": emitted(finished, plan, child), "refusals": negatives,
        "external_accesses": len(audit),
    }


def execute(request):
    data = wire(request)
    command = (sys.executable, "-I", "-B", str(HERE), "--worker")
    first, second = (subprocess.run(command, input=data, capture_output=True, timeout=160) for _ in range(2))
    require(first.returncode == second.returncode == 0, (first.stderr + second.stderr).decode())
    require(first.stdout == second.stdout, "two separated guarded composition workers disagreed")
    result = json.loads(first.stdout)
    parent, child = (b64decode(result.pop(role), validate=True) for role in ("parent", "child"))
    return parent, child, {"request_sha256": fingerprint(data), "parent_sha256": fingerprint(parent),
                           "child_sha256": fingerprint(child), "parent_bytes": len(parent),
                           "child_bytes": len(child), **result}


def independent(model):
    look = replace(
        model,
        DataDirectory=r"C:\IndependentRender\data", StartAppearanceId=(1 << 32) + 97, EmptyBomOnWire=False,
        MainRgb=(35, 139, 203), HiddenLineRgb=(17, 31, 43), LegacyMaterialName="", LegacySpecular=0.25,
        ClassicValue=ClassicLook("defaultplastic", 3, 1, 0.25, 0.625, 0.0078125, 0.015625, False, True),
        ShaderValue=BasicPbrInput("2025x", "basic", (67, 123, 209), (80, 88, 136), (11, 32, 53),
                                  0.25, 0.375, 0.75, 0.5, 3.0, 64.25, 1.375, False, True))
    return asdict(look)


def child_history(source, generated, observed, built, reg):
    roots = tuple(replay(archive, reg)[0].head["root"] for archive in (source, generated))
    changes, forward_aliases = compare_typed(*roots)
    _, reverse_aliases = compare_typed(*roots[::-1])
    holder = "visStateKeyData_c/f78/0/attrs/0/objs/0/o/visStateVisualPropertiesAttribute_c/f10/"
    expected = {holder + "moVisualProperties_c/f20/f90/f00": [
        row["appearance_roles"]["holder"]["realview_id"][0] for row in (observed, built)
    ]}
    for index, (before, after) in enumerate(zip(observed["linked_features"],
                                               built["linked_features"], strict=True), 1):
        prefix = f"visStateKeyData_c/f78/{index}/ref/moCompFeature_c/ff0/"
        expected.update({prefix + "f00": [before[0], after[0]], prefix + "f08": [before[2], after[2]]})
    require(changes == expected and not forward_aliases and not reverse_aliases,
            "child store differs outside validated feature keys, creation times and holder allocation: " + repr(changes))
    return changes


def source_case_request(disclosures, phase, pins, parent_report, label_report, audit):
    directory = disclosures / "ConcentricMateSourcePacket02/Disclosed/D01"
    lock = json.loads(checked(directory / "lock.json", LOCK))
    author = json.loads(checked(directory / "author.json", AUTHOR))
    require(lock["source_locked"] and not lock["heldout_source_locked"]
            and author["passed"] and author["result"]["passed"]
            and tuple(lock["native_artifacts"][phase.lower()][role]["sha256"]
                      for role in ("parent", "child")) == pins,
            "appearance evidence is outside the exact disclosed source custody")
    folder = directory / "Native" / phase
    parent, raw, shape = source_case(folder, *FILES, pins)
    projected = project_d01(parent, raw, shape)
    archive = SldprtArchive.from_bytes(checked(folder / FILES[1], pins[1]))
    reg = registry()
    appearance, roles = request_look(archive, reg)
    original = child_store(archive, reg, rich=True)
    definition = source_definition(archive)
    single = source_store(raw, audit["cases"]["D01" + phase]["visual"])
    source_label = owned_label(shape.native.LinkValue)
    require(not original["provisional_schemas"] and single["state_name"] == projected.display_name
            and source_label["mode"] == "radius",
            "D01 appearance does not have its strict supported typed source roles")
    refusal = refused(lambda: ReadAsmModel(parent), "assembly root contains unprojected model content")
    destination = str(PureWindowsPath(r"C:\KitD01ChildAppearance") / phase / FILES[0])
    neutral = model_request(projected, EPOCH, destination)
    sketch, = projected.child.document.sketches
    label = RadialLabelIn(sketch.id, sketch.parameter_ids[0], source_label["text"])
    appearance_value = replace(from_json(appearance), StartAppearanceId=1)
    request = {**neutral, "radial_label": asdict(label), "appearance": asdict(appearance_value)}
    parent_bytes, child_bytes, fresh = execute(request)
    compare_root(projected, parent_bytes, fresh)
    generated, _ = role_document(child_bytes, fresh["mate"]["body_atom_id"])
    mapped, cap_roles = reversible_child(projected, shape, generated)
    typed = owned_label(ReadNativeLink(SldprtArchive.from_bytes(child_bytes), 0))
    historical = child_history(archive, SldprtArchive.from_bytes(child_bytes),
                               original, fresh["child_store"], reg)
    actual = fresh["appearance"]
    require(actual["physical_density_parameter"] is None
            and actual["active_configuration_density"] == roles["store"]["active_configuration_density"] == -1.0
            and roles["store"]["physical_density_parameter"] == [1000.0, 0]
            and (actual["holder_id"], actual["model_and_configuration_id"], actual["definition_next_appearance_id"])
            == (1, 2, 3) and definition["list_count"] == 0 and typed["text"] == source_label["text"]
            and fresh["child_store"]["appearance_roles"]["holder"]["resource_locator"]
            == original["appearance_roles"]["holder"]["resource_locator"],
            "D01 surface presentation no longer agrees with its separate source and generated owners")
    for name in ("realview_roughness", "dspbr_roughness", "packed_colour", "dspbr_field_count"):
        require(original["appearance_roles"]["holder"][name] == fresh["child_store"]["appearance_roles"]["holder"][name],
                "D01 renderer semantic check drifted: " + name)
    require([row[1] for row in original["linked_features"]] ==
            [row[1] for row in fresh["child_store"]["linked_features"]]
            and set(mapped) and len(cap_roles) == 3 and parent_report["whole_source_refusal"] == refusal
            and label_report["source_typed_view"]["text"] == list(source_label["text"]),
            "separate label, child feature roles or legacy source guard diverged")
    return request, {
        "source_parent_sha256": pins[0], "source_child_sha256": pins[1],
        "source_appearance": roles, "source_definition": definition, "source_child_store": original,
        "source_parent_store": single, "whole_source_refusal": refusal, "source_radial_text": source_label["text"],
        "generated_radial_text": typed["text"], "mapped_design_roles": len(mapped), "mapped_brep_faces": len(cap_roles),
        "complete_child_store_historical_delta": historical,
        **fresh,
    }


def run(disclosures, controls):
    measurements = REPO / "re/solidworks/measurements/2026"
    audit = json.loads(checked(measurements / "ConcentricDisplayState01.json", DISPLAY_AUDIT))
    parents = (controls / "ParentCurrent.json").read_bytes()
    require((controls / "ParentBase.json").read_bytes() == parents, "existing singleton construction changed")
    labels = {}
    for phase in (*D01_LOCKED, "RightContrast"):
        current = (controls / f"LabelCurrent-{phase}.json").read_bytes()
        require((controls / f"LabelBase-{phase}.json").read_bytes() == current,
                "existing spatial radial construction changed")
        labels[phase] = {"sha256": fingerprint(current), "rows": json.loads(current)}
    cases = {}
    varied = None
    for phase, pins in D01_LOCKED.items():
        request, cases[phase] = source_case_request(disclosures, phase, pins, json.loads(parents)["cases"][phase],
                                                   labels[phase]["rows"], audit)
        if phase == "Source":
            request["appearance"] = independent(from_json(dict(request["appearance"])))
            _, _, varied = execute(request)
            style = varied["appearance"]
            require(varied["parent_sha256"] == cases[phase]["parent_sha256"]
                    and varied["child_sha256"] != cases[phase]["child_sha256"]
                    and style["primary_rgb"] == [35, 139, 203]
                    and style["classic_roughness"] == 0.625 and style["dspbr_roughness"] == 0.375
                    and style["reflectance"] == 0.25 and style["holder_id"] == (1 << 32) + 97
                    and style["definition_next_appearance_id"] == (1 << 32) + 99,
                    "independent appearance contrast did not follow the authored optical inputs")
    return {
        "schema": "kit.sw2026.d01-child-appearance.v1", "base": BASE, "source_build": "34.5.2.0604",
        "source_lock_sha256": LOCK, "source_author_sha256": AUTHOR, "written_at": EPOCH,
        "cases": cases, "independent_authored_shader_contrast": varied, "guarded_composition_workers": 6,
        "legacy_reports_byte_identical": {"parent_display": fingerprint(parents),
                                          **{"radial_label_" + phase: row["sha256"] for phase, row in labels.items()}},
        "tool_sha256": fingerprint(HERE.read_bytes()), "new_native_processes": 0, "new_heldout_credit": 0,
        "runtime_external_accesses": 0, "public_write_qualified": False, "whole_source_admitted": False,
    }


def main():
    parser = ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--worker", action="store_true")
    mode.add_argument("--disclosures", type=Path)
    parser.add_argument("--controls", type=Path)
    args = parser.parse_args()
    if args.worker:
        sys.stdout.buffer.write(wire(worker(json.load(sys.stdin))))
    else:
        require(args.controls is not None, "provide the independently guarded baseline and current reports")
        print(json.dumps(run(args.disclosures, args.controls), indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
