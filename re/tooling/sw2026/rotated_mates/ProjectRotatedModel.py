from dataclasses import replace

from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblySysIn import AssemblySysIn
from convert.adapters.solidworks.Archive.Construction.Assembly.System.AsmVocabulary import KAsmFolders
from convert.adapters.solidworks.Archive.Construction.Header.HeaderInput import HeaderInput
from convert.adapters.solidworks.Archive.Construction.Metadata.HistoryInput import HistoryInput
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import FeatureTarget
from convert.adapters.solidworks.Archive.Construction.Presentation.StyleInput import StyleInput
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import RectDimInput
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import PrincipalFrame
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import ModelDefInput
from interchange.assembly.AssemblyEnums import ComponentKind, MateAlignment, MateEntityKind, MateKind
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.assembly.MateConstraint import MateConstraint
from interchange.assembly.MateEntity import MateEntity
from interchange.assembly.MateGroup import MateGroup
from interchange.assembly.TransformMatrix import TransformMatrix
from interchange.document.Models.DocumentModel import AssemblyData, CadDocument, ComponentDoc
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.geometry.Models.Sketch import ConstraintRef, SketchRelation
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.Records.RecordSource import CadSource

from tests.Convert.Solidworks.PlainWriting.MakePlainDoc import MakePlainDoc


def require(condition, message):
    if not condition:
        raise ValueError(message)


def length(metres):
    return ParameterValue(1000 * metres, ValueKind.KLength, "mm")


def planes(scope, names):
    rows = []
    for axis in "xyz":
        frame = PrincipalFrame(axis)
        transform = Transform(*(SpaceVector(*value) for value in (
            frame.OriginValue, frame.AxisU, frame.AxisV, frame.NormalValue
        )))
        rows.append(SupportPlane(f"{scope}/plane/{axis}", names[axis], transform))
    return tuple(rows)


def child_document(child):
    spec = child["document"]
    require(spec["plane_axis"] == "z", "the cited child needs the Front datum")
    points = tuple(tuple(1000 * value for value in row) for row in spec["vertices_m"])
    document = MakePlainDoc(spec["name"], points, 1000 * spec["depth_m"])
    (sketch,) = document.sketches
    (feature,) = document.feature_timeline
    vertices = spec["vertices_m"]
    lengths = tuple(max(row[axis] for row in vertices) - min(row[axis] for row in vertices) for axis in (0, 1))
    parameters = tuple(Parameter(f"child/parameter/{index}", f"D{index + 1}", length(value),
                                 owner_id=sketch.id) for index, value in enumerate(lengths))
    axis_rules = tuple(
        SketchRelation(f"child/axis/{index}", "horizontal" if index % 2 == 0 else "vertical",
                       (ConstraintRef(line.id),)) for index, line in enumerate(sketch.entities)
    )
    length_rules = tuple(
        SketchRelation(f"child/dimension/{index}", "distance",
                       (ConstraintRef(line.id, "start"), ConstraintRef(line.id, "end")), driver.id)
        for index, (line, driver) in enumerate(zip(sketch.entities[:2], parameters, strict=True))
    )
    child_planes = planes("child", child["presentation"]["plane_names"])
    return replace(
        document,
        configurations=(replace(document.configurations[0], name=spec["configuration_name"]),),
        support_planes=child_planes,
        sketches=(replace(sketch, name=spec["sketch_name"], support_plane_id=child_planes[2].id,
                          parameter_ids=tuple(row.id for row in parameters),
                          constraints=axis_rules + length_rules),),
        feature_timeline=(replace(feature, name=spec["extrusion_name"]),),
        bodies=(replace(document.bodies[0], name=spec["extrusion_name"]),),
        parameters=(*parameters, *document.parameters),
    )


def occurrence_rows(bundle, root_id, leaf):
    rows = []
    authored_mates = bundle["mates"]
    (fixed,) = {row["fixed_occurrence"] for row in authored_mates}
    for index, value in enumerate(bundle["occurrences"]):
        place = value["placement"]
        u, v = place["u"], place["v"]
        w = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
        matrix = tuple(coordinate
                       for axes in zip(u, v, w, (1000 * item for item in place["origin"]), strict=True)
                       for coordinate in axes) + (0.0, 0.0, 0.0, 1.0)
        rows.append(ComponentInst(f"instance/{index}", value["name"], leaf.id, root_id,
                                  TransformMatrix(matrix), index, configuration_name=leaf.configuration_name,
                                  configuration_id=leaf.configuration_id, fixed=index == fixed))
    return tuple(rows)


def mate_rows(authored, root_id, occurrences, child):
    entities, mates, drivers = [], [], []
    datum_ids = {datum.name: datum.id for datum in child.support_planes}
    for order, row in enumerate(authored):
        key = f"mate/{order}"
        owner_ids = []
        for index, value in enumerate(row["endpoints"]):
            identity = f"{key}/entity/{index}"
            occurrence = occurrences[value["occurrence"]]
            entities.append(MateEntity(identity, root_id, (occurrence.id,), MateEntityKind.PLANE,
                                       source_entity_id=datum_ids[value["datum"]]))
            owner_ids.append(identity)
        kind = MateKind(row["kind"])
        distance, parameters = None, ()
        if kind is MateKind.DISTANCE:
            distance = length(row["distance_m"])
            driver = Parameter(f"{key}/D1", "D1", distance, ParameterRole.KDriving, owner_id=key)
            drivers.append(driver)
            parameters = (driver.id,)
        mates.append(MateConstraint(key, row["name"], kind, root_id, tuple(owner_ids), order,
                                    distance, parameters, MateAlignment(row["alignment"])))
    return tuple(entities), tuple(mates), tuple(drivers)


def author_model(bundle):
    assembly = bundle["assembly"]
    child = child_document(bundle["child"])
    root_config = Configuration("root/config", assembly["configuration_name"], True)
    (child_config,) = child.configurations
    root = ComponentDef("assembly/root", assembly["name"], ComponentKind.ASSEMBLY,
                        configuration_name=root_config.name, configuration_id=root_config.id)
    leaf = ComponentDef("assembly/child", bundle["child"]["document"]["name"], ComponentKind.PART,
                        document_id="document/child", configuration_name=child_config.name,
                        configuration_id=child_config.id, body_ids=tuple(body.id for body in child.bodies))
    instances = occurrence_rows(bundle, root.id, leaf)
    entities, mates, drivers = mate_rows(bundle["mates"], root.id, instances, child)
    group = MateGroup("group/mates", assembly["mate_group_name"], root.id, tuple(mate.id for mate in mates))
    graph = AssemblyData(root.id, (root, leaf), instances, (ComponentDoc(leaf.document_id, child),),
                         entities, mates, (group,))
    model = CadDocument(CadSource("kit-neutral", "<authored rotated assembly>", "0" * 64),
                        (root_config,), drivers, planes("root", assembly["presentation"]["assembly_features"]["plane_names"]),
                        (), (), (), (), assembly=graph, metadata={"name": assembly["name"]})
    model.assert_valid()
    return model


def authored_common(spec, checked):
    presentation = spec["presentation"]
    style, units, header, target = (presentation["styles"], presentation["units"],
                                    spec["provenance"], spec["target"])
    settings = presentation.get("definition", presentation)
    return {
        "StyleValue": StyleInput(style["standard"], style["font_name"], style["line_style_name"],
                                 style["language_id"], tuple(style["print_widths_m"]),
                                 tuple(style["exclusion_names"]), tuple(style["task_labels"]),
                                 tuple(style["cutlist_expressions"])),
        "DocumentUnits": UnitInput(units["length_unit"], units["angle_unit"],
                                   units["unit_system"], units["decimal_places"]),
        "TargetValue": FeatureTarget(target["date_code"], target["parasolid_version"]),
        "HeaderValue": HeaderInput(header["author"], header["company"], header["comment"],
                                   header["created_at"], header["modified_at"], header["modified_at"]),
        "HistoryValue": HistoryInput(header["created_at"], header["comment"],
                                     header["originating_build_code"], header["license_origin"],
                                     style["language_id"], presentation["cjk_saved"]),
        "DefinitionValue": ModelDefInput(settings["drafting_standard"], tuple(settings["detail_flags"]),
                                         tuple(settings["tessellation"]), settings["system_preference_7a"],
                                         settings["journal_name"], checked.TargetValue.FileVersion),
        "OutputValue": replace(checked.OutputValue, SavedAt=spec["output"]["saved_at"]),
    }


def literal_recipes(bundle, plan):
    leaf, root = bundle["child"], bundle["assembly"]
    leaf_styles = leaf["presentation"]
    leaf_document = leaf["document"]
    leaf_input = plan.ChildRecipe
    leaf_system = replace(leaf_input.SystemValue,
                          FolderValues=tuple((kind, leaf_styles["folder_names"][kind])
                                             for kind in leaf_styles["folder_order"]),
                          PlaneNames=tuple((axis, leaf_styles["plane_names"][axis]) for axis in "xyz"),
                          CabinetName=leaf_styles["cabinet_name"], OriginName=leaf_document["origin_name"],
                          CreatedAt=leaf["provenance"]["created_at"])
    child = replace(leaf_input, SystemValue=leaf_system, HatchName=leaf_styles["hatch_name"],
                    DensityValue=leaf_document["density_kg_m3"], DesignIntent=leaf_styles["design_intent"],
                    SelectedLeader=leaf_styles["selected_leader"], **authored_common(leaf, leaf_input))
    rect = leaf_document["rectangle_dimensions"]
    dimensions = RectDimInput(tuple(rect["width_text_m"]), tuple(rect["height_text_m"]),
                              child.DesignIntent, child.SelectedLeader, rect["route_centerline"])
    root_style = root["presentation"]["assembly_features"]
    root_system = AssemblySysIn(tuple((kind, root_style["folder_names"][kind]) for kind in KAsmFolders),
                                tuple((axis, root_style["plane_names"][axis]) for axis in "xyz"),
                                root_style["cabinet_name"], root["origin_name"], root["mate_group_name"],
                                root["provenance"]["created_at"])
    root_input = plan.RootRecipe
    parent = replace(root_input, SystemValue=root_system,
                     SavePartValues=root["presentation"]["definition"]["save_as_part_preferences"],
                     **authored_common(root, root_input))
    return parent, child, dimensions
