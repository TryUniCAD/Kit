import argparse
from dataclasses import asdict, replace
from hashlib import sha256
import json
from math import isclose, pi
from pathlib import Path, PureWindowsPath
import sys


SW2026 = Path(__file__).resolve().parents[2]
REPO = SW2026.parents[2]
sys.path[:0] = [str(REPO / "src"), str(SW2026), str(SW2026 / "serial")]

from ConcentricNativeContract import checked, digest, require, write_json
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import FeatureInstant
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import SetCfgStampMut
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.MakeCirclePart import MakeCirclePart
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectCircle import ProjectCircle
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadPrincAxis import ReadPrincAxis
from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import LightInput
from convert.adapters.solidworks.Archive.Construction.System.Members.MakeLightMut import MakeLightMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import ReadAsmModel
from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadLightInput import ReadLightInput
from convert.adapters.solidworks.Core.TypedResolved.Circles.ReadLocalCirc import ReadLocalCirc
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadChildren import ReadChildren
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange import frozen_mapping
from interchange.geometry.Models.GeometryCurves import CircleGeometry, PointGeometry
from interchange.serialization.Deserialize import FromData
from interchange.serialization.EncodeData import ToData
from para.EmitAttachedPart import emit_attached_part


SCHEMA = "kit.sw2026.disclosed-radial-scene-intent.v1"
SOURCE_PARENT = "2267cb6bc7e02d05be19ce5105ba3e43240eb4d1ad897647237dc875445d0dc2"
SOURCE_CHILD = "92b83376b42ca55aa3b32a350635585c788ea0f968cc6e54f1730fdeb3c99caa"
SOURCE_FEATURE_NEUTRAL = "e5e005dc738ad379f0485accc78d7f72002cccdc1b14186ea43ed82e4f444fe3"


def radial_from_archive(link):
    (profile,) = [row for row in IndexFeatures(link).values() if row.ClassValue.NameValue == "moProfileFeature_c"]
    local, driver = ReadLocalCirc(profile.FieldsValue["pd_f80"], link)
    require(driver is not None and local.ModeValue == "radius", "the actual native sketch requires a driving radius")
    return local, driver


def light_values(light):
    data = asdict(light)
    data.pop("CreatedValue")
    return data


def source_scene(link):
    environment = link.ConfigValue.RootValue.FieldsValue["f1e0"]
    require(environment.ClassValue.NameValue == "moEnvFolder_c", "missing actual configuration environment owner")
    lights = tuple(ReadLightInput(row) for row in ReadChildren(environment))
    require(tuple(row.KindValue for row in lights) == ("ambient", "directional", "directional", "directional"),
            "the disclosed ordinary four-light scene is required")
    return ReadNodeName(environment), lights


def child_intent(source, native_circle, native_driver):
    (sketch,) = source.sketches
    (arc,) = [row for row in sketch.entities if type(row.geometry) is CircleGeometry]
    (center,) = [row for row in sketch.entities if type(row.geometry) is PointGeometry]
    require(len(sketch.entities) == 2 and center.geometry.point == arc.geometry.center
            and not arc.construction and not center.construction and not sketch.suppressed
            and sketch.closed_profile_entity_ids == ((arc.id,),), "source circle centre or profile ownership is unresolved")
    radius_rule, fixed_rule = sketch.constraints
    require(str(radius_rule.kind) == "radius" and str(fixed_rule.kind) == "fixed"
            and [(ref.entity_id, ref.point) for ref in radius_rule.references] == [(arc.id, "")]
            and [(ref.entity_id, ref.point) for ref in fixed_rule.references] == [(center.id, "")]
            and fixed_rule.parameter_id is None and all(row.driving and not row.suppressed for row in sketch.constraints),
            "source does not keep the complete fixed-centre radius relation")
    params = {row.id: row for row in source.parameters}
    (boss,) = [row for row in source.feature_timeline if str(row.kind) == "extrusion"]
    radial = params[radius_rule.parameter_id]
    (depth_id,) = boss.parameter_ids
    depth = params[depth_id]
    require(len(params) == 2 and str(source.units) == "mm" and len(source.bodies) == 1 and not source.materials
            and str(radial.role) == str(depth.role) == "driving" and radial.name == depth.name == "D1"
            and radial.value.unit == depth.value.unit == "mm" and radial.expression is depth.expression is None
            and sketch.parameter_ids == (radial.id,) and boss.sketch_id == sketch.id and depth.owner_id == boss.id
            and depth.value == boss.definition.length and not boss.suppressed
            and str(boss.definition.end_condition) == "blind" and not boss.definition.reversed and not boss.definition.symmetric
            and boss.definition.second_length is None and boss.definition.second_end_condition is None
            and all(value is None for value in (boss.definition.offset, boss.definition.draft_angle,
                                                boss.definition.second_offset, boss.definition.second_draft_angle))
            and not boss.definition.up_to_reference and not boss.definition.second_up_to_reference,
            "source driving owner or ordinary blind end is unresolved")
    source_plane = next(row for row in source.support_planes if row.id == sketch.support_plane_id)
    (configuration,) = source.configurations
    require(configuration.active and not configuration.overrides and not configuration.suppressed_feature_ids
            and source_plane.name == "Front Plane" and ReadPrincAxis(source_plane.transform) == "z",
            "source does not keep its actual ordinary support and active configuration")
    values = (arc.geometry.center.x, arc.geometry.center.y, arc.geometry.radius)
    measured = (*native_circle.CenterValue, native_circle.RadiusValue)
    require(all(isclose(a, b, rel_tol=1e-12, abs_tol=1e-12) for a, b in zip(values, measured, strict=True))
            and isclose(radial.value.value, native_driver.value_mm, rel_tol=1e-12)
            and isclose(radial.value.value, arc.geometry.radius, rel_tol=1e-12),
            "public and typed native radius values disagree")
    neutral_path = checked(REPO / "re/solidworks/inputs/ConcentricFeatureNeutral01.json", SOURCE_FEATURE_NEUTRAL)
    seed = FromData(json.loads(neutral_path.read_bytes())).assembly.documents[0].document
    seed_sketch, seed_boss = seed.sketches[0], seed.feature_timeline[0]
    seed_radial = next(row for row in seed.parameters if row.owner_id == seed_sketch.id)
    seed_depth = next(row for row in seed.parameters if row.owner_id == seed_boss.id)
    constraints = tuple(replace(row, kind="radius") if row.parameter_id == seed_radial.id else row for row in seed_sketch.constraints)
    child = replace(
        seed,
        metadata=frozen_mapping({"name": "DisclosedRadialSceneProbe"}),
        configurations=(replace(seed.configurations[0], name=configuration.name),),
        support_planes=(replace(seed.support_planes[0], name=source_plane.name, transform=source_plane.transform),),
        sketches=(replace(seed_sketch, name=sketch.name, constraints=constraints,
                          entities=(replace(seed_sketch.entities[0], geometry=arc.geometry),)),),
        parameters=(replace(seed_radial, name=radial.name, value=radial.value), replace(seed_depth, name=depth.name, value=depth.value)),
        feature_timeline=(replace(seed_boss, name=boss.name, definition=replace(seed_boss.definition, length=depth.value)),),
        bodies=(replace(seed.bodies[0], name=boss.name),),
    )
    child.AssertValid()
    return child, {"sketch": sketch.id, "profile_arc": arc.id, "fixed_center": center.id,
                   "radius_parameter": radial.id, "boss": boss.id, "depth_parameter": depth.id}


def project(parent_file, child_file, output):
    from convert import open_document

    checked(parent_file, SOURCE_PARENT)
    checked(child_file, SOURCE_CHILD)
    document = open_document(parent_file, include_brep=True, include_tessellation=False)
    source = document.assembly.documents[0].document
    require(source.source.sha256 == SOURCE_CHILD and document.metadata["solidworks.typed_mates_semantics"]["status"] == "admitted",
            "the disclosed public parent and complete typed mate are required")
    try:
        ReadAsmModel(document)
    except ValueError as error:
        root_refusal = str(error)
    else:
        raise ValueError("the whole-source admission boundary changed")
    link = ReadNativeLink(SldprtArchive.from_bytes(child_file.read_bytes()), 0)
    native_circle, native_driver = radial_from_archive(link)
    environment, lights = source_scene(link)
    child, bindings = child_intent(source, native_circle, native_driver)
    output.mkdir(parents=True, exist_ok=False)
    request = {"schema": SCHEMA, "child": ToData(child), "environment_name": environment,
               "lights": [light_values(row) for row in lights]}
    write_json(output / "IndependentRequest.json", request)
    proof = {"schema": SCHEMA, "parent_sha256": SOURCE_PARENT, "child_sha256": SOURCE_CHILD,
             "request_sha256": digest(output / "IndependentRequest.json"), "dimension_owners": bindings,
             "actual_light_creation_instants": [asdict(row.CreatedValue) for row in lights],
             "source_parent_feature_rows": len(document.feature_timeline),
             "source_occurrences": [(value.name, value.reference_number) for value in document.assembly.instances],
             "source_selected_faces": [(value.instance_path, value.source_entity_id) for value in document.assembly.mate_entities],
             "source_refusals": [root_refusal, "unqualified source B-rep identity and presentation mapping",
                                 "unqualified concentric radius-child attachment and parent construction",
                                 "source dimension annotation placement and full scene chronology are outside this part probe"],
             "source_accepted": False, "heldout_inputs_read": 0, "native_processes_started": 0}
    write_json(output / "Projection.json", proof)
    return proof


def read_intents(rows, written_at):
    lights = []
    for index, row in enumerate(rows, 1):
        values = dict(row)
        if values["DirectionValue"] is not None:
            values["DirectionValue"] = tuple(values["DirectionValue"])
        lights.append(LightInput(**values, CreatedValue=FeatureInstant(written_at, index)))
    return tuple(lights)


def attach_scene(part, lights, target):
    folder = part.SystemValue.SystemValues.FolderValues["moEnvFolder_c"]
    require(folder is part.SystemValue.RootValue.FieldsValue["f1e0"] and not ReadChildren(folder), "scene owner must be fresh and empty")
    parents = part.HeaderValue, part.TopHeader
    cursor = parents[0].FieldsValue["f08"]
    require(parents[1].FieldsValue["f08"] == cursor, "model and top header allocator cursors differ")
    allocator = PersistentIds(cursor)
    members = [MakeLightMut(folder, value, target, allocator) for value in lights]
    folder.FieldsValue["f60"] = {"list": {"n": len(members), "items": [{"o": row} for row in members]}, "tail": 0}
    for header in parents:
        header.FieldsValue["f08"] = allocator.NextValue
    SetCfgStampMut(part.CurrentConfig, allocator)
    return emit_attached_part(part)


def check_archives(part, base, plan, lights):
    archive = SldprtArchive.from_bytes(part.BytesValue)
    link = ReadNativeLink(archive, 0)
    circle, driver = radial_from_archive(link)
    require(isclose(driver.value_mm, plan.CircleValue.RadiusValue * 1000, rel_tol=1e-12)
            and isclose(circle.RadiusValue, driver.value_mm, rel_tol=1e-12), "generated radius intent differs")
    _, actual = source_scene(link)
    require(actual == lights, "generated scene changes actual ordered light intent or writer chronology")
    config = link.ConfigValue
    resolved = link.ResolvedValue
    config_raw, map_graph = WriteConfigMut(config.RootValue, 19000, config.HeaderValue)
    resolved_raw, _ = WriteResolMut(resolved.RootsValue, resolved.ExtraFields, 19000, map_graph.MapValue, resolved.ContextValue)
    regenerated = {"Contents/Config-0": config_raw, "Contents/Config-0-ResolvedFeatures": resolved_raw}
    for name in ("Header2", "Contents/Config-0-ModelHeader"):
        regenerated[name] = WriteHeadGraph(ReadHeaderGraph(archive.require(name), 19000), 19000)
    regenerated["Contents/CMgr"] = WriteCmgrMut(ReadCmgrMut(archive.require("Contents/CMgr"), 19000).RootValue, 19000)
    for name, payload in regenerated.items():
        require(payload == archive.require(name), "inexact typed re-emission: " + name)
    require(set(base.StreamsValue) == set(part.StreamsValue), "lighting changed stream inventory")
    changed = sorted(key for key in base.StreamsValue if base.StreamsValue[key] != part.StreamsValue[key])
    return {"linked_stream_bytes": {name: len(payload) for name, payload in regenerated.items()},
            "changed_streams_vs_light_free": changed,
            "config_growth_bytes": len(config_raw) - len(base.StreamsValue["Contents/Config-0"]),
            "source_scope": "standalone disclosed radial and four-light discriminator"}


def build(request_path, expected, output, native_destination, written_at):
    import codecs

    data = json.loads(checked(request_path, expected).read_bytes())
    require(set(data) == {"schema", "child", "environment_name", "lights"} and data["schema"] == SCHEMA, "unexpected intent envelope")
    document = FromData(data["child"])
    plan = ProjectCircle(document)
    require(plan.AxisValue == "z" and plan.PlaneName == "Front Plane" and not plan.IsDiameter
            and plan.EndValue.ModeValue == "blind" and not plan.EndValue.IsReversed,
            "standalone discriminator requires the explicit forward Front radius plan")
    destination = PureWindowsPath(native_destination)
    require(destination.is_absolute() and destination.name == plan.NameValue + ".SLDPRT", "native destination must match its owned neutral name")
    recipe = MakePartRecipe(plan, written_at)
    root_names = tuple((kind, data["environment_name"] if kind == "moEnvFolder_c" else name)
                       for kind, name in recipe.SystemValue.FolderValues)
    recipe = replace(recipe, SystemValue=replace(recipe.SystemValue, FolderValues=root_names))
    bound = BindPartIntent(document, plan, recipe, SelfFileInput(str(destination), written_at))
    lights = read_intents(data["lights"], written_at)
    require(tuple(row.KindValue for row in lights) == ("ambient", "directional", "directional", "directional"), "complete four-light scene required")
    for encoding in ("utf-16-le", "utf-16-be", "utf-8", "cp1252"):
        codecs.lookup(encoding)
    attempted = []
    active = True

    def guard(event, _):
        if active and event in {"open", "subprocess.Popen", "os.system", "os.posix_spawn", "socket.connect"}:
            attempted.append(event)
            raise RuntimeError("guarded part construction attempted runtime I/O: " + event)

    sys.addaudithook(guard)
    try:
        base = MakeCirclePart(document, bound)
        first = attach_scene(MakeCirclePart(document, bound), lights, bound.TargetValue)
        second = attach_scene(MakeCirclePart(document, bound), lights, bound.TargetValue)
        require(first.BytesValue == second.BytesValue, "same semantic request did not generate identical output")
        proof = check_archives(first, base, plan, lights)
    finally:
        active = False
    require(not attempted, "guarded part operation attempted runtime I/O")
    radius = plan.CircleValue.RadiusValue
    x, y = plan.CircleValue.CenterValue
    geometry = {}
    for label, depth in (("initial", plan.DepthValue), ("planned_depth_edit", plan.DepthValue * 1.173)):
        geometry[label] = {"bodies": 1, "radius_m": radius, "depth_m": depth,
                           "volume_m3": pi * radius**2 * depth, "area_m2": 2 * pi * radius * (radius + depth),
                           "centre_of_mass_m": (x, y, depth / 2)}
    output.mkdir(parents=True, exist_ok=False)
    native_file = output / destination.name
    native_file.write_bytes(first.BytesValue)
    proof.update(request_sha256=expected, output_sha256=sha256(first.BytesValue).hexdigest(),
                 runtime_io_attempts=len(attempted), ordered_lights=[row.NameValue for row in lights],
                 native_processes_started=0, native_acceptance=False,
                 generated_part_only=True, independent_prediction=geometry)
    write_json(output / "Build.json", proof)
    return proof


def main():
    parser = argparse.ArgumentParser(description="Project and build a disclosed radial child with explicit light semantics")
    commands = parser.add_subparsers(dest="command", required=True)
    projection = commands.add_parser("project")
    projection.add_argument("--parent", type=Path, required=True)
    projection.add_argument("--child", type=Path, required=True)
    projection.add_argument("--output", type=Path, required=True)
    writer = commands.add_parser("build")
    writer.add_argument("--request", type=Path, required=True)
    writer.add_argument("--sha256", required=True)
    writer.add_argument("--output", type=Path, required=True)
    writer.add_argument("--native-destination", required=True)
    writer.add_argument("--written-at", type=int, required=True)
    args = parser.parse_args()
    if args.command == "project":
        result = project(args.parent.resolve(strict=True), args.child.resolve(strict=True), args.output)
    else:
        result = build(args.request, args.sha256, args.output, args.native_destination, args.written_at)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
