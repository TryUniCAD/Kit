from dataclasses import dataclass
from math import isclose

from CheckConcentricSourceBrep import map_source_endpoints
from ProjectConcentricRadialIntent import radial_from_archive, source_scene

from convert.adapters.solidworks.Archive.Construction.Assembly.System.AsmVocabulary import KAsmFolders
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadPrincAxis import ReadPrincAxis
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadNodeName, ReadRows
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.AssemblyPreparation.Concentric.BindConcSide import ReadConcSide
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import ReadAsmModel
from convert.adapters.solidworks.Core.Preparation.Circle.PlanCircle import PlanCircle
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadLightInput import ReadLightInput
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadNotesInput import ReadNotesInput
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadChildren import ReadChildren
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.assembly.AssemblyData import AssemblyData
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.assembly.MateConstraint import MateConstraint
from interchange.assembly.MateEntity import MateEntity
from interchange.assembly.MateGroup import MateGroup
from interchange.document.Models.DocumentModel import CadDocument, ComponentDoc
from interchange.Enums.EnumDocument import Capability
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import CircleGeometry, PointGeometry
from interchange.geometry.Models.Sketch import ConstraintRef, Sketch, SketchEntity, SketchRelation
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Parameter
from interchange.Records.RecordSource import CadSource


@dataclass(frozen=True)
class ProjectedPart:
    document: CadDocument
    side_id: str
    scene: str
    lights: tuple
    identities: dict


@dataclass(frozen=True)
class RootSettings:
    name: str
    folders: tuple
    cabinet: str
    origin: str
    lights: tuple
    notes: object


@dataclass(frozen=True)
class ProjectedDesign:
    document: CadDocument
    child: ProjectedPart
    settings: RootSettings
    display_name: str
    axes: tuple
    identities: dict


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def active_config(document):
    config, = document.configurations
    require(config.active is True and config.parent_id is None and not config.overrides
            and not config.suppressed_feature_ids, "projection requires one unsuppressed active configuration")
    return config


def neutral_config(config):
    return Configuration("configuration/active", config.name, active=True)


def neutral_plane(row):
    require(row.support_selection_id is None and row.offset_parameter_id is None
            and row.attributes.get("principal") is True, "projection requires a real independent principal datum")
    return SupportPlane("datum/" + ReadPrincAxis(row.transform), row.name, row.transform)


def neutral_source():
    return CadSource("kit.neutral", "", "")


def owned_child(child_info, child_definition):
    child = child_info.child
    sketch, = child.sketches
    arc, = [row for row in sketch.entities if isinstance(row.geometry, CircleGeometry)]
    center, = [row for row in sketch.entities if isinstance(row.geometry, PointGeometry)]
    radius_rule, fix_rule = sketch.constraints
    require(len(sketch.entities) == 2 and sketch.closed_profile_entity_ids == ((arc.id,),)
            and not (arc.construction or center.construction or sketch.suppressed)
            and center.geometry.point == arc.geometry.center,
            "projection requires the sole closed circle and its actual separate centre")
    require(
        radius_rule.kind == "radius" and radius_rule.references == (ConstraintRef(arc.id),)
        and fix_rule.kind == "fixed" and fix_rule.references == (ConstraintRef(center.id),)
        and fix_rule.parameter_id is None
        and all(row.driving and not row.suppressed for row in (radius_rule, fix_rule)),
        "projection requires the precise native radius and separately fixed centre owners",
    )
    steps = {row.id: row for row in child.feature_timeline}
    body, = child.bodies
    boss = steps[child_info.producer]
    profile, = [row for row in steps.values() if row.sketch_id == sketch.id and row.id != boss.id]
    support, = [row for row in child.support_planes if row.id == sketch.support_plane_id]
    neutral_support = neutral_plane(support)
    datum, = [row for row in steps.values() if row.attributes["native_object_id"] == support.attributes["native_object_id"]]
    require(profile.name == sketch.name and profile.input_feature_ids == (datum.id,)
            and boss.input_feature_ids == (profile.id,) and body.final_feature_id == boss.id
            and not (profile.suppressed or profile.selection_ids or profile.configuration_states
                     or boss.suppressed or boss.selection_ids or boss.configuration_states)
            and body.name == boss.name and body.material_id is None and not child.materials,
            "projection requires datum to profile to boss to implicit body ownership")
    by_parameter = {row.id: row for row in child.parameters}
    radial, = [row for row in by_parameter.values() if row.id == radius_rule.parameter_id]
    depth, = [row for row in by_parameter.values() if row.id in boss.parameter_ids]
    local, native_radius = radial_from_archive(child_info.native.LinkValue)
    link = child_info.native.LinkValue
    feature = child_info.native.FeatureValue
    bound_boss = ReadExtrude(link, feature, IndexFeatures(link))
    native_depth = bound_boss.RequireDepth().DepthValue
    require(
        len(by_parameter) == 2 and profile.parameter_ids == sketch.parameter_ids == (radial.id,)
        and radial.owner_id == profile.id and depth.owner_id == boss.id
        and radial.name == native_radius.name == depth.name == native_depth.name == "D1"
        and radial.attributes["typed_archive_owner"] == native_radius.TypedOwner
        and depth.attributes["typed_archive_owner"] == native_depth.TypedOwner
        and isclose(depth.value.value, native_depth.value_mm, rel_tol=1e-12)
        and FieldInt(bound_boss.ProfileValue.FieldsValue, "f08") == profile.attributes["native_object_id"]
        and not (bound_boss.IsReversed or bound_boss.SecondValue)
        and radial.value.unit == depth.value.unit == "mm" and depth.value == boss.definition.length
        and radial.expression is depth.expression is None
        and str(radial.role) == str(depth.role) == "driving"
        and isclose(radial.value.value, native_radius.value_mm, rel_tol=1e-12)
        and isclose(arc.geometry.radius, local.RadiusValue, rel_tol=1e-12),
        "projection requires independent linked native radius and depth drivers",
    )
    config = active_config(child)
    require(child_definition.document_id and child_definition.body_ids == (body.id,)
            and child_definition.configuration_name == config.name
            and child_definition.name == ReadNodeName(child_info.native.LinkValue.ConfigValue.RootValue),
            "projection requires the child definition to own its actual document and body")
    circle = SketchEntity("profile/circle", arc.kind, arc.geometry)
    neutral_sketch = Sketch(
        "sketch/profile", sketch.name, neutral_support.id, (circle,),
        constraints=(
            SketchRelation("relation/radius", "radius", (ConstraintRef(circle.id),), "driver/radius"),
            SketchRelation("relation/fixed-centre", "fixed", (ConstraintRef(circle.id, "center"),)),
        ),
        parameter_ids=("driver/radius",), closed_profile_entity_ids=((circle.id,),),
    )
    neutral_boss = FeatureStep(
        "feature/boss", boss.name, boss.kind, 0, sketch_id=neutral_sketch.id,
        parameter_ids=("driver/depth",), operation=BooleanOp.KCreate, definition=boss.definition,
    )
    neutral_body = DesignBody("body/solid", body.name, neutral_boss.id)
    result = CadDocument(
        neutral_source(), (neutral_config(config),), (
            Parameter("driver/radius", radial.name, radial.value, radial.role, owner_id=neutral_sketch.id),
            Parameter("driver/depth", depth.name, depth.value, depth.role, owner_id=neutral_boss.id),
        ),
        (neutral_support,), (neutral_sketch,), (), (neutral_boss,), (neutral_body,),
        capabilities=frozenset((
            Capability.KParameters, Capability.KParamHistory, Capability.KSupportPlanes,
            Capability.KEditableSketches, Capability.KBodyStructure, Capability.KConfigurations,
        )),
        metadata={"name": child_definition.name}, units=child.units,
    )
    side, _ = ReadConcSide(result, PlanCircle(result, Measured=True))
    scene, lights = source_scene(child_info.native.LinkValue)
    identities = {
        "configuration": (config.id, result.configurations[0].id),
        "front_support": (support.id, neutral_support.id),
        "sketch_feature": (profile.id, neutral_sketch.id),
        "sketch": (sketch.id, neutral_sketch.id),
        "circle": (arc.id, circle.id),
        "fixed_centre": (center.id, (circle.id, "center")),
        "radius_relation": (radius_rule.id, "relation/radius"),
        "fixed_relation": (fix_rule.id, "relation/fixed-centre"),
        "radius_driver": (radial.id, "driver/radius"),
        "blind_depth_driver": (depth.id, "driver/depth"),
        "boss": (boss.id, neutral_boss.id),
        "body": (body.id, neutral_body.id),
        "lateral_face": (child_info.side_face, side.id),
    }
    return ProjectedPart(result, side.id, scene, lights, identities)


def model_settings(link):
    model = link.ConfigValue.RootValue
    roots = link.ResolvedValue.RootsValue
    folders = {node.ClassValue.NameValue: ReadNodeName(node) for node in roots if node.ClassValue.NameValue in KAsmFolders}
    require(len(folders) == len(KAsmFolders), "projection requires the complete ordinary parent folder roles")
    env, = [node for node in roots if node is model.FieldsValue["f1e0"]]
    lights = tuple(ReadLightInput(row) for row in ReadChildren(env))
    cabinet, = [node for node in roots if node.ClassValue.NameValue == "moDetailCabinet_c"]
    notes = ReadNotesInput(ReadChildren(cabinet))
    origin, = [node for node in roots if node.ClassValue.NameValue == "moOriginProfileFeature_c"]
    exploded = model.FieldsValue["f1590"]
    require(exploded.ClassValue.NameValue == "moExplViewManager_c"
            and exploded.FieldsValue["f358"] is None and exploded.FieldsValue["f360"] is None
            and exploded.FieldsValue["f368"]["n"] == 0
            and not ReadRows(exploded.FieldsValue["f368"]["items"])
            and exploded.FieldsValue["f398"] == 0.0
            and exploded.FieldsValue["f3a0"] == exploded.FieldsValue["f3a4"] == -1,
            "projection requires its actual empty exploded-view manager")
    return RootSettings(
        ReadNodeName(model), tuple((kind, folders[kind]) for kind in KAsmFolders),
        ReadNodeName(cabinet), ReadNodeName(origin), lights, notes,
    )


def project_d01(parent, raw, source):
    graph = parent.assembly
    require(graph.documents[0].document is source.child, "projection requires the owned original source object")
    endpoints = map_source_endpoints(parent, raw, source, source)
    defs = {row.id: row for row in graph.definitions}
    root_def = defs[graph.root_definition_id]
    ordered_occ = tuple(sorted(graph.instances, key=lambda row: row.order))
    child_def, = [row for row in defs.values() if row is not root_def]
    require(len(ordered_occ) == 2 and all(row.definition_id == child_def.id for row in ordered_occ)
            and graph.documents[0].id == child_def.document_id
            and root_def.kind == "assembly" and child_def.kind == "part"
            and len({row.id for row in ordered_occ}) == 2,
            "projection requires exactly one owned repeated direct child")
    require(all(row.owner_definition_id == root_def.id and row.configuration_name == child_def.configuration_name
                and row.configuration_id == child_def.configuration_id
                and not (row.suppressed or row.hidden or row.flexible or row.exclude_from_bom)
                for row in ordered_occ) and sum(row.fixed for row in ordered_occ) == 1,
            "projection requires matching visible rigid configurations and one fixed occurrence")
    require(tuple(row.order for row in ordered_occ) == (0, 1)
            and tuple(row.name for row in ordered_occ)
            == tuple(child_def.name + "-" + row.reference_number for row in ordered_occ),
            "projection requires actual canonical occurrence names and explicit order")
    child = owned_child(source, child_def)
    config = active_config(parent)
    require(root_def.configuration_name == config.name, "source root definition differs from its active configuration")
    root_id, child_id, document_id = "definition/assembly", "definition/part", "document/part"
    occurrences = tuple(
        ComponentInst(f"occurrence/{row.order + 1}", row.name, child_id, root_id, row.transform,
                      row.order, row.reference_number, row.configuration_name,
                      child.document.configurations[0].id, fixed=row.fixed)
        for row in ordered_occ
    )
    occ_ids = {old.id: new.id for old, new in zip(ordered_occ, occurrences, strict=True)}
    source_mate, = graph.mates
    source_group, = graph.mate_groups
    require(source_group.owner_definition_id == root_def.id and not source_group.parent_group_id
            and source_group.mate_ids == (source_mate.id,) and source_group.order == 0,
            "projection requires the actual unique ordered mate group")
    entities = tuple(
        MateEntity(f"endpoint/{index}", root_id, (occ_ids[row["occurrence"]],),
                   "cylinder", source_entity_id=child.side_id, radius=source.radius)
        for index, row in enumerate(endpoints, 1)
    )
    mate = MateConstraint("mate/concentric", source_mate.name, source_mate.kind, root_id,
                          tuple(row.id for row in entities), alignment=source_mate.alignment,
                          attributes={"rotation_locked": source_mate.attributes["rotation_locked"]})
    group = MateGroup("group/mates", source_group.name, root_id, (mate.id,))
    planes = tuple(neutral_plane(row) for row in parent.support_planes)
    require(len(planes) == 3 and {row.id for row in planes} == {"datum/x", "datum/y", "datum/z"},
            "projection requires the three actual independent parent datums")
    assembly = AssemblyData(
        root_id,
        (ComponentDef(root_id, root_def.name, root_def.kind, configuration_name=config.name,
                      configuration_id=neutral_config(config).id),
         ComponentDef(child_id, child_def.name, child_def.kind, document_id=document_id,
                      configuration_name=child_def.configuration_name,
                      configuration_id=child.document.configurations[0].id, body_ids=(child.document.bodies[0].id,))),
        occurrences, (ComponentDoc(document_id, child.document),), entities, (mate,), (group,),
    )
    neutral = CadDocument(
        neutral_source(), (neutral_config(config),), (), planes, (), (), (), (),
        capabilities=frozenset((Capability.KAssemblies, Capability.KAssemblyMates, Capability.KComponentDocs,
                                Capability.KConfigurations, Capability.KSupportPlanes)),
        metadata={"name": root_def.name}, units=parent.units, assembly=assembly,
    )
    ReadAsmModel(neutral)
    link = ReadNativeLink(SldprtArchive.from_bytes(raw), 0)
    settings = model_settings(link)
    display, = parent.assembly.attributes["display_states"]
    native_display = dict(display["native_attributes"])
    require(native_display["swShowState"] == "Yes,Yes," and display["name"] == native_display["swDisplayStateName"],
            "projection requires its actual single all-visible display state")
    identities = {
        "root_definition": (root_def.id, root_id), "child_definition": (child_def.id, child_id),
        "embedded_document": (child_def.document_id, document_id),
        "configuration": (config.id, neutral.configurations[0].id),
        "occurrences": tuple(occ_ids.items()), "mate_group": (source_group.id, group.id),
        "mate": (source_mate.id, mate.id),
        "endpoints": tuple((row["entity"], end.id) for row, end in zip(endpoints, entities, strict=True)),
        "principal_planes": tuple((row.id, plane.id) for row, plane in zip(parent.support_planes, planes, strict=True)),
    }
    return ProjectedDesign(neutral, child, settings, display["name"],
                           tuple(row["local_axis"] for row in endpoints), identities)
