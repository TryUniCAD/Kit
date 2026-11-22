from argparse import ArgumentParser
from base64 import b64decode, b64encode
import codecs
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import json
from math import isclose
from pathlib import Path, PureWindowsPath
import subprocess
import sys
from types import SimpleNamespace


REPO = Path(__file__).resolve().parents[5]
TOOLS = REPO / "re/tooling/sw2026"
sys.path[:0] = [str(REPO / "src"), str(TOOLS), str(TOOLS / "serial"), str(Path(__file__).resolve().parent)]

from CheckConcentricAssembly import verify_emission
from CheckConcentricSourceBrep import map_source_endpoints, match_cylinder_shapes, read_cylinder_roles
from ProjectConcentricRadialIntent import light_values, read_intents
from ProjectD01Concentric import model_settings, owned_child, project_d01, require
from ProveConcentricSourceBrep import D01_LOCKED, checked, json_digest, source_case

from convert import open_document
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Construction.Assembly.Displays.AsmDisplayIn import AsmDisplayIn
from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import FeatureInstant
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.MakeCylAsm import MakeCylAsm
from convert.adapters.solidworks.Archive.Construction.System.Members.NotesInput import NotesInput
from convert.adapters.solidworks.Assembly.Assembly import DecodeNativeAsm
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.AssemblyPreparation.Children.ReadAsmPlanes import ReadAsmPlanes
from convert.adapters.solidworks.Core.AssemblyPreparation.Concentric.PlanCylMate import PlanCylMate
from convert.adapters.solidworks.Core.AssemblyPreparation.Concentric.PrepCylChild import PrepCylChild
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import ReadAsmModel
from convert.adapters.solidworks.Core.AssemblyPreparation.Paths.ReadAsmPaths import ReadAsmPaths
from convert.adapters.solidworks.Core.AssemblyPreparation.Placements.ReadAsmPlace import ReadAsmPlace
from convert.adapters.solidworks.Core.AssemblyPreparation.Recipe.MakeAsmRecipe import MakeAsmRecipe
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CylChild import CylChild
from convert.adapters.solidworks.Core.TypedMates.Cylinders.PickCylFace import PickCylFace
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylNodes import ReadCylNodes
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylOwner import ReadCylOwner
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.ReadRadialDrive import ReadRadialDrive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.geometry.Models.GeometryCurves import CircleGeometry, PointGeometry
from interchange.serialization.Deserialize import FromData
from interchange.serialization.EncodeData import ToData


BASE = "8ea2fa45b285499f1f50c61f04b29c7f0649ebf4"
LOCK = "bdd8bf3782ccf01991a3ac402da2923f2d320728792fb8ccb500f73189e9f90b"
AUTHOR = "2db426555837d4ef400c478c89ca6f94a63b5b200f555d5dafbeee8a557688be"
FILES = ("ConcentricD01AlignedFree.SLDASM", "ConcentricD01Child.SLDPRT")
VISUAL = "ThirdPtyStore/VisualStates"
DISPLAY_ERROR = "assembly visibility requires the default and two opposite states"


def fingerprint(data):
    return sha256(data).hexdigest()


def model_request(projected, written_at, destination):
    settings = projected.settings
    return {
        "purpose": "disclosed concentric design correspondence",
        "document": ToData(projected.document),
        "written_at": written_at,
        "destination": destination,
        "endpoint_local_axes": projected.axes,
        "child_scene": projected.child.scene,
        "child_lights": [light_values(row) for row in projected.child.lights],
        "root_model_name": settings.name,
        "root_folders": settings.folders,
        "root_cabinet": settings.cabinet,
        "root_origin": settings.origin,
        "root_lights": [light_values(row) for row in settings.lights],
        "root_notes": (settings.notes.HeadName, settings.notes.EndName),
        "root_empty_exploded_view": True,
        "root_display_name": projected.display_name,
    }


def proof_guard():
    for encoding in ("utf-16-le", "utf-16-be", "cp1252", "utf-8", "ascii"):
        codecs.lookup(encoding)
    attempts = []

    def guard(event, args):
        if (event in ("open", "os.listdir", "os.scandir", "os.system", "os.fork", "os.posix_spawn")
            or event.startswith(("socket.", "subprocess.", "ctypes.", "winreg."))
            or (event == "import" and args[0].split(".")[0] in ("pythoncom", "win32com", "FreeCAD", "adsk"))):
            attempts.append(event)
            raise RuntimeError("concentric model worker attempted external access: " + event)

    sys.addaudithook(guard)
    return attempts


def worker(request):
    require(request["purpose"] == "disclosed concentric design correspondence"
            and request["root_empty_exploded_view"] is True, "unknown research generation request")
    epoch = request["written_at"]
    document = FromData(request["document"])
    model = ReadAsmModel(document)
    paths = ReadAsmPaths(model.RootValue.name, model.ChildValue.name, request["destination"], epoch)
    axes = tuple(tuple(row) for row in request["endpoint_local_axes"])
    child_lights = read_intents(request["child_lights"], epoch)
    root_lights = read_intents(request["root_lights"], epoch)
    notes = NotesInput(*request["root_notes"], FeatureInstant(epoch, 5), FeatureInstant(epoch, 6))
    GetDocumentCaps(model.ChildDocument)
    attempts = proof_guard()
    child = PrepCylChild(model.ChildDocument, paths.ChildValue, request["child_scene"], child_lights)
    plan = PlanCylMate(document, model.ChildDocument, child.CandidateValue, child.FaceTag)
    root = MakeAsmRecipe(model, MakePartRecipe(child.CandidateValue.PlanValue, epoch), ReadAsmPlanes(document), paths.ParentValue)
    system = replace(root.SystemValue, FolderNames=tuple(tuple(row) for row in request["root_folders"]),
                     CabinetName=request["root_cabinet"], OriginName=request["root_origin"],
                     LightValues=root_lights, NotesValue=notes, HasEmptyExplodedView=True)
    root = replace(root, ModelName=request["root_model_name"], SystemValue=system)
    operands = (plan.CandidateValue, root, plan.Placements, plan.EndIndexes, child.FaceTag,
                replace(plan.MateInput, LocalAxes=axes))
    display = AsmDisplayIn(request["root_display_name"], tuple((row.name, not row.hidden) for row in model.Occurrences))
    try:
        MakeCylAsm(*operands, DisplayValues=(display,))
    except ValueError as error:
        require(str(error) == DISPLAY_ERROR, "unexpected source display rejection: " + str(error))
    else:
        raise ValueError("the exact source display gate opened and needs a new full comparison")
    diagnostic = MakeCylAsm(*operands)
    require(not attempts and diagnostic.ChildValue is child.CandidateValue, "unexpected runtime access or a crossed child")
    atom, = child.CandidateValue.SystemValue.RootValue.FieldsValue["fd88"]["atoms"]
    feature_body = atom["o"].FieldsValue["f140"]
    child_bridge = SimpleNamespace(candidate=child.CandidateValue, atom_id=feature_body,
                                   projection=SimpleNamespace(lateral_face_tag=child.FaceTag))
    mate = model.GraphValue.mates[0]
    checked_mate = verify_emission(
        diagnostic.BytesValue, child_bridge, plan.MateInput.AlignmentCode,
        mate.attributes["rotation_locked"], model.FixedIndex,
        tuple(plan.ModelValue.Occurrences[index].name for index in plan.EndIndexes),
        expected_local_axes=axes,
    )
    return {
        "child": b64encode(child.CandidateValue.BytesValue).decode("ascii"),
        "parent": b64encode(diagnostic.BytesValue).decode("ascii"),
        "display_refusal": DISPLAY_ERROR,
        "mate": checked_mate,
        "writer_external_accesses": len(attempts),
    }


def role_document(data, atom_id):
    document = open_document(BytesIO(data), source_format="solidworks.sldprt", include_brep=True, strict=True)
    archive = SldprtArchive.from_bytes(data)
    native = ReadNativeLink(archive, 0)
    nodes = ReadCylNodes(archive)
    side, surface, _ = PickCylFace(nodes)
    feature, arc = ReadCylOwner(native, atom_id)
    shape = CylChild(native, nodes, side, surface, feature, arc, atom_id, fingerprint(data))
    return read_cylinder_roles(document, shape), archive


def target_roles(shape):
    document = shape.child
    config, = document.configurations
    sketch, = document.sketches
    circle, = [row for row in sketch.entities if isinstance(row.geometry, CircleGeometry)]
    centre, = [row for row in sketch.entities if isinstance(row.geometry, PointGeometry)]
    radius, fixed = sketch.constraints
    support, = [row for row in document.support_planes if row.id == sketch.support_plane_id]
    radial, = [row for row in document.parameters if row.id == radius.parameter_id]
    depth, = [row for row in document.parameters if row.owner_id == shape.producer]
    require(sketch.parameter_ids == (radial.id,) and radial.owner_id != depth.owner_id
            and radius.kind == "radius" and radius.references[0].entity_id == circle.id
            and fixed.kind == "fixed" and fixed.references[0].entity_id == centre.id
            and centre.geometry.point == circle.geometry.center, "generated circle lost an actual separate edit owner")
    return {
        "configuration": config.id, "front_support": support.id, "sketch_feature": radial.owner_id,
        "sketch": sketch.id, "circle": circle.id, "fixed_centre": centre.id, "radius_relation": radius.id,
        "fixed_relation": fixed.id, "radius_driver": radial.id, "blind_depth_driver": depth.id, "boss": depth.owner_id,
        "body": document.bodies[0].id, "lateral_face": shape.side_face,
    }


def reversible_child(projected, source, generated):
    identities = projected.child.identities
    target = target_roles(generated)
    require(set(identities) == set(target), "generated and source role inventories differ")
    lineage = {role: (*entry, target[role]) for role, entry in identities.items()}
    forward = {(role, row[0]): (row[1], row[2]) for role, row in lineage.items()}
    reverse = {(role, row[2]): (row[0], row[1]) for role, row in lineage.items()}
    require(len(forward) == len(reverse) == len(lineage)
            and all(reverse[(role, target_id)] == (source_id, neutral_id)
                    for (role, source_id), (neutral_id, target_id) in forward.items()),
            "source to model to native child identities are not reversible by role")
    face_ids = match_cylinder_shapes(source, generated)
    require(face_ids[source.side_face] == target["lateral_face"] and len(face_ids) == len(set(face_ids.values())) == 3,
            "physical cap and side roles collide")
    source_drivers = {row.id: row.value for row in source.child.parameters}
    measured = {row.id: row.value for row in generated.child.parameters}
    require(all(source_drivers[lineage[role][0]] == measured[lineage[role][2]]
                for role in ("radius_driver", "blind_depth_driver")), "source and replay driver values differ")
    return lineage, face_ids


def selected_dimension_labels(shape):
    link = shape.native.LinkValue
    boss = shape.native.FeatureValue
    owned = ReadExtrude(link, boss, IndexFeatures(link))
    sketch = owned.ProfileValue.FieldsValue["pd_f80"]
    radial, mode, _ = ReadRadialDrive(link, sketch)
    require(mode == "radius", "the shared label comparison needs the actual radius owner")
    index = radial.TypedOwner["display_index"]
    radial_view, = [entry.EntryValue for entry in link.ResolvedValue.MapValue.EntriesValue
                    if entry.IndexValue == index]
    require(radial_view.ClassValue.NameValue == "moDisplayRadialDim_c",
            "radius text does not have the actual radial display owner")
    return {
        role: tuple(display.FieldsValue["f6a0"]["f38"][key] for key in ("x", "y", "z"))
        for role, display in (("radius", radial_view), ("depth", owned.RequireDepth().DisplayValue))
    }


def source_extras(parent, child, parent_raw, child_raw, display_refusal):
    parent_archive = SldprtArchive.from_bytes(parent_raw)
    child_archive = SldprtArchive.from_bytes(child_raw)
    parent_manager = ReadCmgrMut(parent_archive.require("Contents/CMgr"), 19000).RootValue
    child_manager = ReadCmgrMut(child_archive.require("Contents/CMgr"), 19000).RootValue
    require(VISUAL in parent_archive.streams and VISUAL in child_archive.streams,
            "source display and appearance store inventory changed")
    for case, operand in (("parent", parent), ("child", child)):
        require(not operand.materials and not operand.meshes, "unhandled source material or mesh in " + case)
    try:
        ReadAsmModel(parent)
    except ValueError as error:
        require(str(error) == "assembly root contains unprojected model content", "unexpected whole-source refusal")
        root_refusal = str(error)
    else:
        raise ValueError("original source unexpectedly entered whole-assembly admission")
    return {
        "original_root_refusal": root_refusal,
        "explicit_display_generation_refusal": display_refusal,
        "source_visual_store_bytes": {label: len(archive.require(VISUAL)) for label, archive in
                                      (("parent", parent_archive), ("child", child_archive))},
        "source_manager_visual_locator_present": [bool(node.FieldsValue["f1f8"]) for node in (parent_manager, child_manager)],
        "child_presentation_and_appearance_pending": True,
        "source_clocks_used_as_output_values": False,
        "source_metadata_preserved_outside_construction_input": True,
        "whole_source_admitted": False,
    }


def rejected_sources(parent, raw, shape):
    graph = parent.assembly
    one, two = graph.mate_entities
    crossed = replace(one, instance_path=two.instance_path)
    cap = next(iter(shape.rims.values())).cap_face
    negatives = {
        "crossed_occurrence": replace(parent, assembly=replace(graph, mate_entities=(crossed, two))),
        "cap_as_lateral": replace(parent, assembly=replace(graph, mate_entities=(replace(one, source_entity_id=cap), two))),
    }
    results = {}
    for name, altered in negatives.items():
        try:
            project_d01(altered, raw, shape)
        except ValueError as error:
            results[name] = str(error)
        else:
            raise ValueError("the original source projector failed to refuse " + name)
    return results


def compare_root(projected, parent_raw, result):
    archive = SldprtArchive.from_bytes(parent_raw)
    native = DecodeNativeAsm(archive, include_tessellation=False)
    link = ReadNativeLink(archive, 0)
    rows = {row.feature_id: row for row in native.occurrences}
    model = ReadAsmModel(projected.document)
    generation_rows = tuple(rows[feature] for feature in result["mate"]["occurrences"])
    mate_names = tuple(f"{row.name}-{row.reference_number}" for row in generation_rows)
    occurrences = {row.id: row for row in model.Occurrences}
    endpoints = {row.id: row for row in model.GraphValue.mate_entities}
    ordered = tuple(occurrences[endpoints[key].instance_path[0]] for key in model.GraphValue.mates[0].entity_ids)
    expected_names = tuple(row.name for row in ordered)
    require(mate_names == expected_names and len({row.object_id for row in generation_rows}) == 2,
            "generated ordered occurrence identity is ambiguous")
    require(ReadNodeName(link.ConfigValue.RootValue) == projected.settings.name
            and len(native.configurations) == 1 and native.configurations[0].name == model.ConfigValue.name,
            "generated root lost actual internal name or configuration")
    for actual, expected in zip(generation_rows, ordered, strict=True):
        frame = ReadAsmPlace(expected).FrameValue
        expected_matrix = (*frame.AxisU, *frame.AxisV, *frame.NormalValue, *frame.OriginValue)
        actual_matrix = (*actual.transform[0:3], *actual.transform[4:7], *actual.transform[8:11], *actual.transform[12:15])
        require(actual.reference_number == int(expected.reference_number)
                and len(actual.transform) == 16
                and all(isclose(first, second, rel_tol=1e-12, abs_tol=1e-12)
                        for first, second in zip(expected_matrix, actual_matrix, strict=True)),
                "serialized occurrence renumbered or changed its rigid pose")
    decoded_settings = model_settings(link)
    require(
        [(row.NameValue, light_values(row)) for row in decoded_settings.lights]
        == [(row.NameValue, light_values(row)) for row in projected.settings.lights]
        and decoded_settings.folders == projected.settings.folders
        and decoded_settings.cabinet == projected.settings.cabinet
        and decoded_settings.origin == projected.settings.origin
        and (decoded_settings.notes.HeadName, decoded_settings.notes.EndName)
        == (projected.settings.notes.HeadName, projected.settings.notes.EndName),
        "generated parent lost one of its understood authored member roles",
    )
    child_id, = {row.definition_id for row in generation_rows}
    definition, = [row for row in native.definitions if row.object_id == child_id]
    require(definition.document_type == "PART" and definition.configuration_name == model.ChildValue.configuration_name,
            "generated ordered references do not share the actual child definition and configuration")
    return generation_rows, definition


def run(oracle, phase, written_at):
    root = oracle / "ConcentricMateSourcePacket02/Disclosed/D01"
    lock = json.loads(checked(root / "lock.json", LOCK))
    author = json.loads(checked(root / "author.json", AUTHOR))
    hashes = D01_LOCKED[phase]
    require(lock["source_locked"] and not lock["heldout_source_locked"] and author["passed"] and author["result"]["passed"]
            and tuple(lock["native_artifacts"][phase.lower()][role]["sha256"] for role in ("parent", "child")) == hashes,
            "input is outside the disclosed hash lock")
    folder = root / "Native" / phase
    parent, raw, shape = source_case(folder, *FILES, hashes)
    before = json_digest(parent), json_digest(shape.child)
    projected = project_d01(parent, raw, shape)
    destination = str(PureWindowsPath(r"C:\KitD01ConcentricBridge") / phase / FILES[0])
    semantic = json.dumps(model_request(projected, written_at, destination), sort_keys=True, allow_nan=False).encode()
    invocation = (sys.executable, "-I", "-B", str(Path(__file__).resolve()), "--worker")
    first = json.loads(subprocess.check_output(invocation, input=semantic))
    second = json.loads(subprocess.check_output(invocation, input=semantic))
    require(first == second and first["writer_external_accesses"] == 0, "independent neutral-only workers differed")
    part_bytes, asm_bytes = (b64decode(first[key], validate=True) for key in ("child", "parent"))
    generated, part_archive = role_document(part_bytes, first["mate"]["body_atom_id"])
    rows, actual_child_definition = compare_root(projected, asm_bytes, first)
    mapped = map_source_endpoints(parent, raw, shape, generated)
    lineage, faces = reversible_child(projected, shape, generated)
    gen_child_info = SimpleNamespace(
        document_id=f"generated/definition/{actual_child_definition.object_id}",
        name=ReadNodeName(generated.native.LinkValue.ConfigValue.RootValue),
        configuration_name=actual_child_definition.configuration_name,
        body_ids=(generated.child.bodies[0].id,),
    )
    recovered = owned_child(generated, gen_child_info)
    require(ToData(recovered.document) == ToData(projected.child.document)
            and recovered.side_id == projected.child.side_id
            and recovered.scene == projected.child.scene
            and tuple(map(light_values, recovered.lights)) == tuple(map(light_values, projected.child.lights)),
            "reverse projection does not recover the same authored child design and ordered light intents")
    require(all(recovered.identities[role] == (row[2], row[1]) for role, row in lineage.items()),
            "reverse extraction changed the actual generated role identities")
    for index, (endpoint, row) in enumerate(zip(mapped, rows, strict=True)):
        require(tuple(first["mate"]["world_axes"][index]) == endpoint["world_axis"]
                and abs(first["mate"]["active_intervals"][index][1] - endpoint["generated_axial_bounds_m"][1]) < 1e-12
                and str(row.reference_number) == endpoint["reference_number"],
                "the emitted mate wrapper disagrees with the source physical occurrence")
    endpoint_links = [
        {
            "source_entity": source_end,
            "neutral_entity": neutral_end,
            "source_occurrence": mapped[index]["occurrence"],
            "neutral_occurrence": dict(projected.identities["occurrences"])[mapped[index]["occurrence"]],
            "generated_occurrence": f"sldasm:instance:{rows[index].object_id}",
            "generated_native_feature": rows[index].feature_id,
            "generated_face": mapped[index]["generated_face"],
        }
        for index, (source_end, neutral_end) in enumerate(projected.identities["endpoints"])
    ]
    require(len({item["generated_occurrence"] for item in endpoint_links})
            == len({item["source_occurrence"] for item in endpoint_links}) == len(endpoint_links) == 2,
            "endpoint mapping has no inverse for each occurrence")
    require(before == (json_digest(parent), json_digest(shape.child)), "original source ownership mutated")
    child_input = checked(folder / FILES[1], hashes[1])
    checked(folder / FILES[0], hashes[0])
    expected_labels = selected_dimension_labels(shape)
    observed_labels = selected_dimension_labels(generated)
    remaining = source_extras(parent, shape.child, raw, child_input, first["display_refusal"])
    remaining["child_dimension_labels_m"] = {
        role: {"source": expected_labels[role], "generated": generated_value}
        for role, generated_value in observed_labels.items()
        if generated_value != expected_labels[role]
    }
    return {
        "base": BASE, "phase": phase, "native_source_lock_sha256": LOCK, "native_source_author_sha256": AUTHOR,
        "original_sha256": dict(zip(("parent", "child"), hashes, strict=True)),
        "neutral_constructor_request_sha256": fingerprint(semantic),
        "child_binding": lineage, "recovered_same_neutral_child": True,
        "physical_face_binding": faces, "assembly_binding": projected.identities,
        "ordered_endpoint_binding": endpoint_links, "ordered_physical_endpoints": mapped,
        "root_model_name": projected.settings.name, "published_root_name": projected.document.metadata["name"],
        "guarded_builder_processes": 2, "writer_external_accesses": first["writer_external_accesses"],
        "candidate_bytes_published": 0, "oracle_processes_started": 0, "protected_inputs_read": 0,
        "native_acceptance": False,
        "comparison_candidate": {"parts_sha256": fingerprint(part_bytes), "parent_sha256": fingerprint(asm_bytes),
                                 "part_bytes": len(part_bytes), "parent_bytes": len(asm_bytes), "part_streams": len(part_archive.streams)},
        "remaining": remaining,
        "refused": rejected_sources(parent, raw, shape),
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--phase", choices=tuple(D01_LOCKED))
    parser.add_argument("--disclosures", type=Path)
    parser.add_argument("--written-at", type=int)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(json.load(sys.stdin)), sort_keys=True, allow_nan=False))
        return
    require(args.phase is not None and args.disclosures is not None and args.written_at is not None,
            "use one disclosed phase and an explicit generation epoch")
    print(json.dumps(run(args.disclosures, args.phase, args.written_at), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
