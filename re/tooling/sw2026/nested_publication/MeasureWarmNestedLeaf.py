from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from pathlib import Path
from subprocess import run
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
TOOLS = HERE.parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), *(str(TOOLS / name) for name in
                ("", "serial", "planar_registry", "imported_body_source", "nested_publication"))]

from MeasureNestedReadback import FrozenReads, checked, digest, git, refusal, require
from PlanarSourceLabels import check_relation
from ProjectDisclosedImport import active_configuration, coordinates
from RectanglePresentation import differences, observe
from SpatialTextMut import actual_displays, compose_text_mut
from WarmLeafBoundary import measure_boundary, near
from convert import open_document
from convert.Geometry.Parasolid import DecodeBrepModel
from convert.adapters.solidworks.Archive.Construction.Blind.BlindZeroFields import KBlindZeroFields
from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import DimensionGraph
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import KAtomLists, KAtomWords
from convert.adapters.solidworks.Archive.Construction.Part.MakeRectDimPart import MakeRectDimPart
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectRectDims import ProjectRectDims
from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadDatumFrame import ReadDatumFrame
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeSketchKeys import MakeSketchKeys
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import RectDimInput
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.AssemblyPreparation.Children.ReadRectDisplay import ReadRectDisplay
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.ReadNestedLeaf import ReadNestedLeaf
from convert.adapters.solidworks.Core.Preparation.CheckPlainScope import CheckPlainScope
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.BindBodyName import BindBodyName
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.BodyNameProof import BodyNameProof
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyKernel import ReadBodyKernel
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadNamedBody import ReadNamedBody
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadOutputAtom import ReadOutputAtom
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadChooserPair import ReadChooserPair
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadFaceReps import ReadFaceReps
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadTwoStockCut import ReadTwoStockCut
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckOriginGeom import CheckOriginGeom
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismRoot import CheckPrismRoot
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismEnd import CheckPrismEnd
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckSingleBoss import CheckSingleBoss
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Checks.CheckBossState import CheckBossState
from convert.adapters.solidworks.Core.TypedResolved.Geometry.MakePrismLines import MakePrismLines
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import ReadPrismFrame
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLineLoop import ReadLineLoop as ReadNativeLineLoop
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadLineDims import ReadLineDims
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import CheckTreeAlias
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.Saved.CheckThinMarks import CheckThinMarks
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.Saved.ReadThinRefs import ReadThinRef
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.document.Models.DocumentCaps import InferCaps
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordSource import CadSource
from interchange.serialization.Deserialize import FromData
from interchange.serialization.EncodeData import ToData
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

BASIS = "22f7e7d7649f2e4ea028e9b1dfdf51448868df24"
SOURCE_TREE = "c56041deca7810851b85dca00e27a266eabf5cf2"
PARTITION = "Contents/Config-0-Partition"
FORMAT = "solidworks.sldprt"
NATIVE = "NestedAssemblyDisclosedReplayNative01.json"
ARCHIVE_AUDIT = "DisclosedNestedAssemblyArchiveAudit01.json"
SDK_CONTROL = "SdkNestedNeutralNative01.json"
PINS = {
    NATIVE: "4253a4ec506d58a421c631f8d9d8cb7a6ce7cba624d54f8e82ebc9814a6f2ae5",
    ARCHIVE_AUDIT: "4f116aeb6b8d7234bf980390c2ee74086fbfbc0c76efc38f2cfd84183f12631b",
    SDK_CONTROL: "aa786c6aa4bc7bdae15662c4b4908205b7a0fda7fdb5bb1bb503594a6b0fb967",
}
BOUND_TOOLS = (
    "re/tooling/sw2026/nested_publication/MeasureNestedReadback.py",
    "re/tooling/sw2026/imported_body_source/ProjectDisclosedImport.py",
    "re/tooling/sw2026/imported_body_source/BuildLocalBodyKernel.py",
    "re/tooling/sw2026/planar_registry/RectanglePresentation.py",
    "re/tooling/sw2026/planar_registry/PlanarSourceLabels.py",
    "re/tooling/sw2026/SpatialTextMut.py",
    "tests/Convert/Solidworks/Research/ConstructionGuard.py",
)
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
TARGET_INSTANT = 1795300000


def wire_sha(value):
    return digest(json.dumps(value, sort_keys=True, allow_nan=False).encode())


def pinned(path, pin, size=None):
    require(path == path.resolve(strict=True), "disclosed research input is redirected")
    return checked(path, pin, size)


def models(workspace, references):
    native = references[NATIVE]
    result = json.loads(pinned(workspace / "NestedAssemblyReopen01/Inspection/DisclosedNestedReopenResults.json",
                                native["raw_native_result_sha256"]))
    require(result["passed"] and result["read_only"] and result["controls_healthy"] and result["input_files_unchanged"]
            and result["oracle_sha256"] == ORACLE and result["heldout_inputs_read"] == 0,
            "native observations are outside the disclosed immutable cohort")
    for case, names in (("N01NestedSingle", ("SinglePlate",)), ("N02MixedRepeated", ("RotorPlate", "TailPlate"))):
        folder = workspace / "NestedAssemblySource01/Results" / case
        author_pin = native["author_record_sha256"][case]
        author = json.loads(pinned(folder / "Author.json", author_pin))
        intent = author["job"]["case"]
        require(author["passed"] and author["job"]["mode"] == "author" and intent["name"] == case
                and intent["split"] == "discovery", "source-intent record is not the disclosed author phase")
        phase, = (row for row in result["phases"] if row["mode"] == "reopen" and row["name"] == case)
        require(phase["passed"] and phase["source_files_unchanged"] and phase["open_errors"] == phase["open_warnings"] == 0,
                "disclosed source did not sustain a clean native read-only reopen")
        for name in names:
            native_observation = phase["initial"]["definitions"][name]
            owner = next(row for row in intent["parts"] if row["name"] == name)
            prior = references[ARCHIVE_AUDIT]["cases"][case]
            source = prior["documents"][name]
            file = author["result"]["saved_files"][name]
            sha = file["sha256"]
            require(prior["source_author_sha256"] == author_pin
                    and source["native_sha256"] == native_observation["sha256"] ==
                    phase["rebuilt"]["definitions"][name]["sha256"] == sha
                    and source["native_bytes"] == file["bytes"] and file["status"] == [True, 0, 0]
                    and native_observation["whats_wrong"] == 0
                    and near(native_observation["dimensions_m"]["D1@Boss-Extrude1"], owner["depth_m"], 1e-15),
                    "file authority differs across original, typed and native observations")
            yield {"mode": "source", "name": name, "file": str(folder / "Author" / (name + ".SLDPRT")),
                   "sha256": sha, "bytes": file["bytes"], "native_observation": native_observation,
                   "author_record_sha256": author_pin, "native_result_sha256": native["raw_native_result_sha256"]}


def controls(workspace, references):
    case, = (row for row in references[SDK_CONTROL]["cases"] if row["case"] == "SdkNestedNeutralNative03")
    folder = workspace / case["case"]
    fixture = json.loads(pinned(folder / "Fixture.json", case["fixture_sha256"]))
    row = fixture["files"]["plate"]
    yield {"mode": "cold", "file": str(folder / "FrozenGenerated" / row["file"]),
           "sha256": row["sha256"], "bytes": row["bytes"]}
    yield {"mode": "ladder", "file": str(ROOT / "re/solidworks/v2026/corpus/ladder/L1_boss.SLDPRT"),
           "sha256": "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6"}
    yield {"mode": "selected", "file": str(workspace / "ThroughMultiStock03/DisclosedNative/ThroughMultiStock.SLDPRT"),
           "sha256": "748cdbec3fe61d6801f3d606e64fe42ecba95e9a647897be3fe3790570a889f3"}


def warm_named_graph(document, archive):
    payloads, _, marks = ReadBodyKernel(archive.require(PARTITION), PARTITION)
    basis = DecodeBrepModel(payloads[0].data)
    require(basis is not None, "selected live partition has no neutral B-rep")
    before_name = replace(document, brep=basis)
    graph = ReadNamedBody(before_name, archive, 0)
    require(BindBodyName(before_name, graph) == document,
            "rebinding the exact selected partition changes the established strict public document")
    return graph, marks


def validate_creator(link, features, atom, boss):
    CheckSingleBoss(features, "moExtrusion_c")
    body = link.ConfigValue.RootValue.FieldsValue
    atom_id = atom.FieldsValue["f140"]
    feature_id = NativeNodeId(boss)
    require(ReadOutputAtom(boss) is atom and atom.FieldsValue["f12c"] == atom.FieldsValue["f130"] == feature_id
            and body["fd88"]["n6c"] == 1 and body["fd88"]["atoms"][0]["o"] is atom
            and body["fd90"]["n"] == 0 and not body["fd90"]["objects"],
            "warm creator must be the actual sole output base and last modifier without any ghost body")
    expected = {"has_f528": 1, "n494": 1, "f540": 3, "f544": 1, "has_f4a8": 1,
                "has_f4b0": 1, "f4b8": 1, "has_f4c0": 1, "has_f3d0": 1}
    fields = boss.FieldsValue
    require(fields["f28"] == 0xC0000140 and fields["f810"] == -1 and fields["f838"] == 0.0
            and fields["f498"] == [{"v": atom_id}]
            and all(fields.get(name) == expected.get(name, 0) for name in KAtomWords)
            and not any(not IsLineState(fields.get(name)) for name in KAtomLists if name != "f498")
            and all(IsLineState(fields.get(name)) for name in ("f368", "f388", "f780"))
            and all(fields.get(name) is None for name in ("f538", "f6e0", "f758"))
            and fields["f7a0"] == 0,
            "warm creator has a selected, consumed or alternate geometry owner")
    return atom_id, feature_id


def check_saved_owners(link, owner, marks):
    boss = owner.NodeValue
    end = owner.EndValue.FieldsValue
    empty = {"n": 0, "items": []}
    require(end["f08"] == end["f128"] == end["has_f28"] == end["has_f48"] == 1
            and all(end[name] == empty for name in ("f28", "f48", "fe0", "f100"))
            and all(end[name] is None for name in ("f20", "fc8", "fd0", "f138", "f90"))
            and end["fa0"] == 0.0
            and all(end[name] == 0 for name in KBlindZeroFields if name not in ("has_f28", "has_f48", "f150", "f154")),
            "saved blind boss has a second direction, direction override, or an end selection")
    CheckThinMarks(link.ConfigValue.RootValue, boss, marks)
    middle = boss.FieldsValue["f4b0"]
    require(middle["f68"] is boss and middle["f48"] == empty,
            "saved boss has a separate body chooser input")
    first = ReadChooserPair(link, boss, "f4a8")
    second = ReadChooserPair(link, boss, "f4c0")
    faces = tuple(ReadFaceReps(row) for row in first)
    require(len(set((*first, *second))) == 4 and faces == tuple(map(ReadFaceReps, second)),
            "saved boss has detached or different mirrored face owners")
    all_reps = tuple(row for face in faces for row in face)
    sources = tuple(ReadThinRef(row, NativeNodeId(boss)) for row in all_reps)
    external = {item for _, item in sources}
    require(len(set(all_reps)) == 10 and len(external) == 1
            and all(tuple(row.ClassValue.NameValue for row in reps) ==
                    ("moEndFaceSurfIdRep_c", *("moFromSktEntSurfIdRep_c",) * 4)
                    and reps[0].FieldsValue["f38"] == index
                    and {row.FieldsValue["f38"] for row in reps[1:]} == {1, 2, 3, 4}
                    for index, reps in enumerate(faces)),
            "saved boss has unrepresented face identities")
    CheckTreeAlias(link, (*all_reps, *(item for item, _ in sources), *external))
    return {"active_and_previous_marks": marks, "concrete_chooser_faces": 4,
            "semantic_face_rep_count": len(all_reps),
            "unclassified_saved_end_words": {name: end[name] for name in ("f150", "f154")}}


def align_support(document, link, features, owner):
    others = {}
    for node in features.values():
        if node.ClassValue.NameValue != "moRefPlane_c":
            continue
        frame, axis = ReadDatumFrame(node)
        plane, = (row for row in document.support_planes if row.attributes["native_object_id"] == NativeNodeId(node))
        require(plane.name == ReadNativeName(node) and not (plane.support_selection_id or plane.offset_parameter_id)
                and coordinates(plane.transform.origin) == tuple(1000 * word for word in frame.OriginValue)
                and tuple(map(coordinates, (plane.transform.x_axis, plane.transform.y_axis, plane.transform.z_axis)))
                == (frame.AxisU, frame.AxisV, frame.NormalValue), "public plane is not its actual typed principal frame")
        others[axis] = plane
    require(set(others) == {1, 2, 3} and len(document.support_planes) == 3, "part has another support domain")
    origin, = (row for row in features.values() if row.ClassValue.NameValue == "moOriginProfileFeature_c")
    CheckOriginGeom(origin)
    front = others[3]
    require(ReadPrismFrame(origin, link.ConfigValue.RootValue, features) == front.transform
            and ReadPrismFrame(owner.ProfileValue, link.ConfigValue.RootValue, features) == front.transform,
            "user sketch or origin leaves the actual front support")
    return front


def project_parameters(document, link, owner, step, profile_step, sketch, native):
    sketch_owner = RequireNative(owner.ProfileValue.FieldsValue["pd_f80"], "sgSketch")
    rows = ReadLineDims(sketch_owner, link)
    require(tuple(row.NameValue for row in rows.DriverValues) == ("D1", "D2")
            and sketch.attributes["typed_archive_owner"] == NativeNodeSpan(link, sketch_owner)
            and profile_step.attributes["typed_archive_owner"] == NativeNodeSpan(link, owner.ProfileValue)
            and step.attributes["typed_archive_owner"] == NativeNodeSpan(link, owner.NodeValue),
            "retained public constraints or profile are outside the actual typed dimension graph")
    native_loop = ReadNativeLineLoop(sketch_owner, link, rows)
    entities = {item.id: item.geometry for item in sketch.entities}
    order, = sketch.closed_profile_entity_ids
    require(len(native_loop.PointsValue) == len(entities) == len(order) == 4
            and tuple(entities[key] for key in order) == MakePrismLines(native_loop),
            "public outline does not use all four local archive lines and points")
    params = []
    display_modes = []
    for driver in rows.DriverValues:
        _, parameter = check_relation(sketch, owner.ProfileValue, profile_step, document, driver)
        require(not parameter.expression and parameter.value.kind == "length"
                and driver.MetresValue == native["dimensions_m"][f"{driver.NameValue}@{sketch.name}"],
                "sketch driver differs from its independent active native API observation")
        params.append(replace(parameter, owner_id=sketch.id, attributes={}, provenance=None))
        fields = driver.DisplayValue.FieldsValue
        require(fields["f6a0"]["f10"] == 18 and fields["f1014"] in (0, 0x800)
                and type(fields["ff80"]) is int,
                "native label has a different presentation owner")
        display_modes.append((bool(fields["fb60"] & 0x100), fields["ff80"], bool(fields["f1014"])))
    require(len(set(display_modes)) == 1, "the two source labels require independent composer preferences")
    depth, = (row for row in document.parameters if row.id in step.parameter_ids)
    native_depth = owner.RequireDepth().DepthValue
    require(depth.owner_id == step.id and depth.name == "D1" and depth.role == "driving"
            and depth.expression is None and depth.value == step.definition.length
            and depth.attributes["typed_archive_owner"] == native_depth.TypedOwner
            and near(depth.value.value, 1000 * native["dimensions_m"][f"D1@{step.name}"])
            and depth.value.value == native_depth.value_mm,
            "public active depth disagrees with its typed or independent native driver")
    return (*params, replace(depth, attributes={}, provenance=None)), display_modes[0]


def public_model(document, archive, job, raw):
    require(len(document.parameters) == 3, "warm nested rectangle requires exactly three real drivers")
    graph, marks = warm_named_graph(document, archive)
    link = graph.LinkValue
    features = IndexFeatures(link)
    boss = RequireNative(features[graph.FeatureId], "moExtrusion_c")
    atom_id, feature_id = validate_creator(link, features, graph.AtomValue, boss)
    owner = ReadExtrude(link, boss, features)
    require(owner.ParentsValue == (owner.ProfileValue,) and not owner.IsReversed and owner.ModeValue == ExtrudeEnd.KBlind
            and owner.SecondValue is None and owner.SecondModeValue is None,
            "warm boss has other parents or a nonordinary live extrusion mode")
    saved_owners = check_saved_owners(link, owner, marks)
    config = active_configuration(document)
    body, = document.bodies
    sketch, = document.sketches
    step, = (item for item in document.feature_timeline if item.id == body.final_feature_id)
    native = job["native_observation"]
    name = ReadNativeName(link.ConfigValue.RootValue)
    require(name == job["name"] and not graph.IsAuthored and graph.NameValue == body.name == step.name
            and type(step.definition) is ExtrudeFeature and step.operation == "join"
            and not (step.suppressed or step.configuration_states or step.selection_ids or sketch.suppressed)
            and step.sketch_id == sketch.id and step.attributes["native_object_id"] == feature_id
            and {item.attributes["native_object_id"] for item in document.feature_timeline} == set(features)
            and len(document.feature_timeline) == len(features) and not any(item.suppressed for item in document.feature_timeline),
            "public timeline does not bind its actual single editable operation and native support rows")
    profile_step, = (item for item in document.feature_timeline if item.id in step.input_feature_ids)
    profile_id = NativeNodeId(owner.ProfileValue)
    require(step.input_feature_ids == (profile_step.id,)
            and profile_step.attributes["native_object_id"] == profile_id == sketch.attributes["native_object_id"]
            and profile_step.sketch_id == sketch.id and profile_step.name == sketch.name,
            "the boss has an unrepresented operation or profile dependency")
    plane = align_support(document, link, features, owner)
    selection, = document.selections
    select_path, = selection.path
    require(sketch.support_plane_id == plane.id and selection.point is None and not selection.attributes
            and dict(selection.query) == {"topology_role": "direction_axis", "native_owner_id": feature_id,
                                         "native_target_id": profile_id}
            and (select_path.entity_kind, select_path.entity_id, select_path.subelement) == ("native", sketch.name, "N_Axis")
            and step.definition.direction in (None, plane.transform.z_axis)
            and not step.attributes["selected_local_ids"] and not step.attributes["native_selection_references"],
            "source direction axis or body selection is outside the one actual sketch normal")
    require(not (document.materials or document.diagnostics or document.meshes or body.material_id
                 or document.metadata["custom_properties"] or document.metadata["document_summary"]
                 or config.attributes["custom_properties"]),
            "native leaf has a separately authored property material or extension")
    parameters, dimension_modes = project_parameters(document, link, owner, step, profile_step, sketch, native)
    neutral_sketch = replace(sketch, attributes={}, provenance=None,
                             entities=tuple(replace(item, attributes={}, provenance=None) for item in sketch.entities),
                             constraints=tuple(replace(item, attributes={}, provenance=None) for item in sketch.constraints))
    neutral = CadDocument(CadSource("kit-neutral", "<warm-leaf-semantic-projection>", "0" * 64),
                          (Configuration(config.id, config.name, True),), parameters,
                          (replace(plane, attributes={}, provenance=None),), (neutral_sketch,), (),
                          (replace(step, order=0, operation=BooleanOp.KCreate, input_feature_ids=(), attributes={},
                                   provenance=None, definition=replace(step.definition, direction=plane.transform.z_axis)),),
                          (DesignBody(body.id, body.name, step.id),), metadata={"name": name}, units=document.units)
    CheckPlainScope(neutral)
    plan = ProjectRectDims(neutral)
    vertices = tuple((1000 * x, 1000 * y) for x, y in plan.VerticesValue)
    result = measure_boundary(document.brep, body.id, vertices, parameters[-1].value.value, native["mass_properties"])
    bounds = body.topology.bounding_box
    require(bounds is not None
            and tuple(zip(coordinates(bounds.minimum), coordinates(bounds.maximum), strict=True)) == result["bounds_mm"]
            and body.topology.solid_count == 1 and body.topology.volume is None and body.topology.surface_area is None,
            "warm public bounds or retained summary differs from the independently verified solid")
    display = observe(raw, sketch.name)
    native_definition = ComponentDef("leaf/" + name, name, "part", configuration_name=config.name,
                                     configuration_id=config.id, body_ids=(body.id,))
    oriented_face = document.brep.faces[0]
    malformed = replace(document.brep, faces=(replace(oriented_face, same_sense=not oriented_face.same_sense), *document.brep.faces[1:]))
    bad_relation = replace(neutral_sketch.constraints[-1], references=neutral_sketch.constraints[-2].references)
    bad_sketch = replace(neutral_sketch, constraints=(*neutral_sketch.constraints[:-1], bad_relation))
    blocked = {
        "cold_model": refusal(lambda: CheckPrismRoot(link.ConfigValue.RootValue), "ValueError",
                              "cache free prism has unqualified model mode flags"),
        "cold_boss": refusal(lambda: CheckBossState(boss), "ValueError", "cache free prism requires its ordinary create boss mode"),
        "cold_end": refusal(lambda: CheckPrismEnd(owner), "ValueError", "cache free prism has unsupported termination options"),
        "unprojected_native_input": refusal(lambda: ReadNestedLeaf(native_definition, document), "ValueError",
                                            "configuration has unsupported inherited or extended state"),
        "detached_manager_atom": refusal(lambda: validate_creator(link, features, replace(graph.AtomValue), boss),
                                         "ValueError", "warm creator must be the actual sole output base and last modifier"),
        "orientation": refusal(lambda: measure_boundary(malformed, body.id, vertices, parameters[-1].value.value),
                               "ValueError", "source face plane does not coincide with its outward box side"),
        "different_dimension_endpoints": refusal(lambda: ProjectRectDims(replace(neutral, sketches=(bad_sketch,))),
                                                  "ValueError", "rectangle axis and distance relations must bind"),
    }
    evidence = {"model_name": name, "configuration": config.name, "creator_id": feature_id, "live_atom_id": atom_id,
                "profile_id": profile_id, "direction_axis_id": selection.id, "source_operation": str(step.operation),
                "projected_operation": str(neutral.feature_timeline[0].operation),
                "side_state": {"source_attributes": sorted(document.source.attributes),
                               "untransferred_metadata": sorted(document.metadata),
                               "retained_payloads": [(row.kind, row.source_stream, len(row.data), row.sha256)
                                                     for row in document.brep_payloads],
                               "configuration_attributes": sorted(config.attributes),
                               "system_rows": len(document.feature_timeline) - 2},
                "name_binding": dict(BodyNameProof(graph)), "saved_owners": saved_owners,
                "geometry": result, "dimension_display": display,
                "parameters_owned": [(item.name, item.owner_id, item.value.value) for item in parameters],
                "source_creator_flags": {name: boss.FieldsValue[name] for name in ("f28", "f544", "has_f548", "has_f530")},
                "refusals": blocked}
    return evidence, {"document": ToData(neutral), "label_points": [display[axis]["text_m"] for axis in ("width", "height")],
                      "dimension_modes": dimension_modes}


def negative(document, archive, mode):
    if mode == "cold":
        require(PARTITION not in archive.streams and document.brep is not None
                and document.feature_timeline[-1].operation == "create",
                "the exact cache-free contrast lost its existing creator or derived B-rep")
        return refusal(lambda: warm_named_graph(document, archive), "SldprtFormat", "required stream is missing")
    link = ReadNativeLink(archive, 0)
    features = IndexFeatures(link)
    if mode == "selected":
        lineage = ReadTwoStockCut(link)
        return {"actual_operations": [(NativeNodeId(node), node.ClassValue.NameValue)
                                      for node in features.values() if node.ClassValue.NameValue in ("moExtrusion_c", "moICE_c")],
                "actual_selected_wrapper": lineage.WrapperValue.ClassValue.NameValue,
                "actual_consumed_untouched_result_atom_ids": [
                    node.FieldsValue["f140"] for node in (lineage.AtomsValue.ConsumedAtom, lineage.AtomsValue.UntouchedAtom,
                                                           lineage.AtomsValue.ResultAtom)],
                "rejected": refusal(lambda: CheckSingleBoss(features, "moExtrusion_c"), "ValueError",
                                    "SOLIDWORKS requires the whole ordinary single boss inventory")}
    graph, _ = warm_named_graph(document, archive)
    actual_features = IndexFeatures(graph.LinkValue)
    boss = actual_features[graph.FeatureId]
    return {"actual_creator_id": graph.FeatureId, "actual_parameter_count": len(document.parameters),
            "actual_scope_flags": {key: boss.FieldsValue[key] for key in ("f28", "f544", "has_f548", "has_f530")},
            "rejected": refusal(lambda: validate_creator(graph.LinkValue, actual_features, graph.AtomValue, boss),
                                "ValueError", "warm creator has a selected, consumed or alternate geometry owner")}


def primed():
    for name in ("ascii", "utf-16-le", "utf-16-be", "cp1252", "latin-1"):
        lookup(name)


def sketch_signature(document):
    sketch, = document.sketches
    order, = sketch.closed_profile_entity_ids
    positions = {identity: index for index, identity in enumerate(order)}
    params = {row.id: row.name for row in document.parameters}
    entities = {row.id: row for row in sketch.entities}
    support, = (row for row in document.support_planes if row.id == sketch.support_plane_id)
    return (
        sketch.name, support.name, support.transform,
        tuple((entities[key].geometry, entities[key].construction, entities[key].fixed) for key in order),
        frozenset((row.kind, tuple((positions[ref.entity_id], ref.point) for ref in row.references),
                   params[row.parameter_id] if row.parameter_id else None, row.driving, row.suppressed)
                  for row in sketch.constraints),
    )


def inspect(job):
    path = Path(job["file"])
    data = pinned(path, job["sha256"], job.get("bytes"))
    primed()
    guard = FrozenReads({path})
    sys.addaudithook(guard.inspect)
    document = open_document(path)
    before = wire_sha(ToData(document))
    archive = SldprtArchive.from_bytes(data)
    if job["mode"] == "source":
        result, request = public_model(document, archive, job, data)
    else:
        result, request = negative(document, archive, job["mode"]), None
    require(before == wire_sha(ToData(document)) and not guard.denied and guard.reads == {path.name},
            "source evidence or guarded native read changed")
    guard.active = False
    pinned(path, job["sha256"], job.get("bytes"))
    return {"file": path.name, "mode": job["mode"], "file_sha256": job["sha256"], "source_wire_sha256": before,
            "files_unchanged": True, "record": result, "request": request,
            **{key: job[key] for key in ("author_record_sha256", "native_result_sha256") if key in job}}


def compose(job):
    document = FromData(job["document"])
    document.assert_valid()
    InferCaps(document)
    document.to_json()
    name = document.metadata["name"]
    config, = document.configurations
    body, = document.bodies
    definition = ComponentDef("leaf/" + name, name, "part", configuration_name=config.name,
                              configuration_id=config.id, body_ids=(body.id,))
    primed()
    guard = BuildAudit(HERE.parent)
    sys.addaudithook(guard.InspectEvent)
    guard.BeginBuild()
    leaf = ReadNestedLeaf(definition, document)
    plan = leaf.PartValue
    output = SelfFileInput("C:\\KitWarmLeafResearch\\" + name + ".SLDPRT", TARGET_INSTANT)
    recipe = replace(MakePartRecipe(plan, TARGET_INSTANT), OutputValue=output)
    width, height = map(tuple, job["label_points"])
    default = ReadRectDisplay(plan, recipe)
    presentation = RectDimInput(width[:2], height[:2], *job["dimension_modes"])
    planar = MakeRectDimPart(leaf.DocumentValue, recipe, presentation)
    direct_sha = digest(planar.BytesValue)
    direct_display = observe(planar.BytesValue)
    dimension_graphs = tuple(DimensionGraph(parameter, dim, item.FieldsValue["f850"][0]["o"], item)
                             for item, dim, parameter in actual_displays(planar.ProfileValue.ProfileValue))
    keys = MakeSketchKeys(dimension_graphs, recipe.DocumentUnits.LengthUnit)
    spatial, _, _, changed_streams = compose_text_mut(planar, recipe, keys, [width, height])
    readback = open_document(spatial.BytesValue, source_format=FORMAT)
    value, = (item for item in readback.feature_timeline if item.id == readback.bodies[0].final_feature_id)
    require(value.name == document.feature_timeline[0].name and value.operation == "create"
            and value.sketch_id == readback.sketches[0].id
            and sketch_signature(readback) == sketch_signature(document)
            and len(readback.sketches[0].constraints) == 6
            and readback.bodies[0].name == body.name and readback.configurations[0].name == config.name
            and tuple((row.name, row.value, row.role) for row in readback.parameters)
            == tuple((row.name, row.value, row.role) for row in document.parameters),
            "generated strict readback lost its true editable dimensions or creator")
    vertices = tuple((1000 * x, 1000 * y) for x, y in plan.VerticesValue)
    metrics = measure_boundary(readback.brep, readback.bodies[0].id, vertices, document.parameters[-1].value.value)
    display = observe(spatial.BytesValue)
    require(all(tuple(display[axis]["text_m"]) == point
                and display[axis]["centerline_route"] == job["dimension_modes"][2]
                for axis, point in zip(("width", "height"), (width, height), strict=True)),
            "spatial composition changed actual label intent")
    require(not guard.DeniedReads and PARTITION not in spatial.StreamsValue, "native construction used runtime data or retained a payload")
    return {"model_name": name, "recipe_epoch": TARGET_INSTANT, "request_sha256": wire_sha(job),
            "planar_sha256": direct_sha, "spatial_sha256": digest(spatial.BytesValue),
            "changed_streams": changed_streams, "geometry": metrics,
            "default_nested_text_xy_m": [default.WidthText, default.HeightText],
            "default_nested_route_centerline": default.RouteCenter,
            "spatial_source_text_xyz_m": [width, height],
            "spatial_source_route_centerline": job["dimension_modes"][2],
            "planar_display": direct_display, "spatial_display": display,
            "runtime_reads": 0, "binary_files_published": 0}


def invoke(mode, job):
    result = run((sys.executable, "-I", "-B", str(HERE), "--worker", mode), input=json.dumps(job),
                 capture_output=True, text=True, timeout=90)
    require(result.returncode == 0 and not result.stderr, result.stderr[-5400:] or "missing fresh worker output")
    return json.loads(result.stdout)


def supervise(workspace):
    require(git("rev-parse", "HEAD:src").decode().strip() == SOURCE_TREE
            and not git("status", "--porcelain", "--", "src"), "research requires the exact clean reader and writer tree")
    recorded = {name: digest(git("show", f"{BASIS}:{name}")) for name in BOUND_TOOLS}
    for name, pin in recorded.items():
        pinned(ROOT / name, pin)
    references = {name: json.loads(pinned(ROOT / "re/solidworks/measurements/2026" / name, pin)) for name, pin in PINS.items()}
    cases, distinct = [], []
    for job in models(workspace, references):
        result = invoke("inspect", job)
        request = result.pop("request")
        construction = invoke("compose", request)
        observed = result["record"]["dimension_display"]
        for method in ("planar", "spatial"):
            construction[method + "_label_differences"] = differences(observed, construction.pop(method + "_display"))
        require(construction["spatial_label_differences"] == []
                and construction["planar_label_differences"] == [
                    {"path": "/height/text_m/2", "source": observed["height"]["text_m"][2], "generated": 0.0}
                ] and observed["height"]["text_m"][2] != 0,
                "comparison did not isolate the original spatial label in the shared rectangle composer")
        result["construction"] = construction
        cases.append(result)
    for job in controls(workspace, references):
        result = invoke("inspect", job)
        require(result.pop("request") is None, "a distinct negative control reached warm preparation")
        distinct.append(result)
    return {"schema": "kit.sw2026.warm-nested-leaf.v1", "reader_revision": BASIS, "source_tree": SOURCE_TREE,
            "tool_sha256": {file.name: digest(file.read_bytes()) for file in (HERE, HERE.with_name("WarmLeafBoundary.py"))},
            "prior_receipts_sha256": PINS, "prior_tools_sha256": recorded, "cases": cases, "distinct_controls": distinct,
            "guarded_fresh_workers": 2 * len(cases) + len(distinct), "native_processes_started": 0,
            "private_inputs_opened": 0, "native_reexport_qualified": False}


def main():
    parser = ArgumentParser()
    parser.add_argument("--disclosed", type=Path)
    parser.add_argument("--worker", choices=("inspect", "compose"))
    args = parser.parse_args()
    if args.worker:
        method = inspect if args.worker == "inspect" else compose
        value = method(json.load(sys.stdin))
    else:
        require(args.disclosed is not None and args.disclosed.is_absolute(), "use the absolute disclosed workspace")
        value = supervise(args.disclosed)
    print(json.dumps(value, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
