from dataclasses import dataclass

from convert.adapters.freecad.Native import CONSTRAINT_KIND_BY_CODE
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import BlindPlan
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.CheckIdentity import (
    CheckIdentity,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceProperty import (
    ReadPropChild,
    RequireEmpty,
    RequireProp,
)
from FcstdRectangleOwners01 import (
    constraint_owners,
    dependency_plan,
    factory_drivers,
    require,
    source_objects,
    value_quantity,
)
from interchange.geometry.Models.Sketch import ConstraintRef, Sketch


@dataclass(frozen=True)
class CornerIntent:
    recipe: BlindPlan
    local_rule_ids: tuple[str, ...]
    axis_rule_ids: tuple[str, ...]
    driver_rule_ids: tuple[str, str]
    origin_rule_id: str
    source_parameter_ids: tuple[str, str, str]
    source_body_name: str
    source_support_id: str


def check_support(sketch, objects):
    owner = sketch.attributes["freecad"]
    properties = owner["properties"]
    (support_key,) = set(properties) & {"Support", "AttachmentSupport"}
    support = ReadPropChild(properties[support_key], "LinkSubList", "LinkSubList")
    require(
        support["attributes"] == {"count": "1"}
        and support.get("children")
        == [{"tag": "Link", "attributes": {"obj": "XY_Plane", "sub": ""}}]
        and owner["dependencies"] == ["XY_Plane"]
        and objects["XY_Plane"]["type_id"] == "App::Plane"
        and sketch.support_plane_id == "freecad:plane:XY_Plane",
        "the sketch must own its actual whole base XY datum",
    )
    CheckIdentity(properties, "Placement")
    CheckIdentity(properties, "AttachmentOffset")
    RequireProp(properties, "MapMode", "Enumeration", "Integer", "5")
    RequireProp(properties, "MapReversed", "Bool", "Bool", "false")
    RequireEmpty(properties, "ExternalGeometry", "LinkSubList", "LinkSubList")


def check_rules(sketch: Sketch, driver_ids: tuple[str, str]):
    rows = constraint_owners(sketch)
    seen = {}
    for rule, row in zip(sketch.constraints, rows, strict=True):
        raw = rule.attributes["freecad"]
        require(
            CONSTRAINT_KIND_BY_CODE.get(int(raw["Type"])) == rule.kind
            and raw.get("IsDriving", "1") == "1"
            and raw.get("IsActive", "1") == "1",
            "constraint kind or active drive differs from its saved rule",
        )
        selected = tuple(
            (
                (record["id"], record["point_code"])
                if record["kind"] == "owned_sketch_entity"
                else (None, 1)
            )
            for record in row["source_owners"]
        )
        portable_refs = tuple(
            ConstraintRef(entity_id, {0: "", 1: "start", 2: "end"}[point])
            for entity_id, point in selected
            if entity_id is not None
        )
        require(
            portable_refs == rule.references,
            "portable constraint operands differ from the native slots",
        )
        signature = (rule.kind, selected, rule.parameter_id)
        require(signature not in seen, "duplicate source constraint ownership")
        seen[signature] = rule.id

    edges = sketch.closed_profile_entity_ids[0]
    pairs = tuple(zip(edges, (*edges[1:], edges[0]), strict=True))
    joins = tuple(("coincident", ((left, 2), (right, 1)), None) for left, right in pairs)
    axes = tuple(
        ("horizontal" if index % 2 == 0 else "vertical", ((edge, 0),), None)
        for index, edge in enumerate(edges)
    )
    lengths = tuple(
        ("distance", ((edge, 0),), parameter)
        for edge, parameter in zip(edges[:2], driver_ids, strict=True)
    )
    anchor = ("coincident", ((edges[0], 1), (None, 1)), None)
    require(
        set(seen) == {*joins, *axes, *lengths, anchor},
        "source must own four endpoint joins, four orthogonality rules, two lengths and the root coincidence",
    )
    return (
        tuple(seen[key] for key in joins),
        tuple(seen[key] for key in axes),
        (seen[lengths[0]], seen[lengths[1]]),
        seen[anchor],
    )


def plan_corner(document, name: str) -> CornerIntent:
    require(
        document.units == "mm" and len(document.configurations) == 1,
        "the source corner proof requires one millimetre part configuration",
    )
    (config,) = document.configurations
    require(
        config.active
        and not config.overrides
        and not config.suppressed_feature_ids
        and config.parent_id is None
        and not config.attributes,
        "the source corner proof requires one unextended active configuration",
    )
    drivers = factory_drivers(document)
    (sketch,) = document.sketches
    (feature,) = document.feature_timeline
    (body,) = document.bodies
    owners = source_objects(document)
    require(
        not any(value["type_id"] == "Spreadsheet::Sheet" for value in owners.values()),
        "the source needs one owned local width-to-depth equation",
    )
    check_support(sketch, owners)
    require(
        not sketch.suppressed
        and feature.operation == "create"
        and feature.input_feature_ids == ()
        and not feature.selection_ids
        and body.final_feature_id == feature.id
        and owners[feature.attributes["freecad"]["name"]]["type_id"] == "PartDesign::Pad",
        "the source depth must drive its actual first Pad and owned body",
    )

    definition = feature.definition
    require(
        definition.second_end_condition is None
        and not definition.up_to_reference
        and not definition.second_up_to_reference
        and all(
            value is None or value_quantity(value)[0] == 0
            for value in (
                definition.offset,
                definition.second_offset,
                definition.draft_angle,
                definition.second_draft_angle,
            )
        ),
        "source corner proof requires one active end without offset or draft",
    )
    dependent = drivers.depth.expression
    source_name = drivers.width.attributes["freecad_constraint"]["Name"]
    height_name = drivers.height.attributes["freecad_constraint"]["Name"]
    source_sketch = sketch.attributes["freecad"]["name"]
    require(
        all(
            label
            and label.isascii()
            and label.isprintable()
            and not any(mark in label for mark in ('"', "@", chr(92)))
            for label in (source_name, height_name, sketch.name, feature.name)
        ),
        "source equation names must bind one unambiguous native scope",
    )
    require(
        dependent is not None
        and dependent.source == f"{source_sketch}.Constraints.{source_name} / 2"
        and dependent.parameter_ids == (drivers.width.id,)
        and drivers.width.expression is None
        and drivers.height.expression is None,
        "the source needs one owned local width-to-depth equation",
    )
    joins, axes, length_rows, origin = check_rules(sketch, (drivers.width.id, drivers.height.id))
    dependency = dependency_plan(document)
    require(
        dependency.typed_dependency_bindings_complete and len(dependency.expressions) == 1,
        "the Pad depth must be the only real source equation",
    )

    lines = tuple(entity.geometry for entity in sketch.entities)
    require(
        all(
            first.end == second.start
            for first, second in zip(lines, (*lines[1:], lines[0]), strict=True)
        ),
        "the saved line endpoints do not close their owned profile",
    )
    vertices = tuple((line.start.x * 0.001, line.start.y * 0.001) for line in lines)
    width, height, depth = drivers.native_values_m
    require(
        vertices == ((0.0, 0.0), (width, 0.0), (width, height), (0.0, height))
        and depth == width / 2,
        "the source loop and cached depth must match the actual owned lengths",
    )
    recipe = BlindPlan(
        name,
        config.name,
        "Front Plane",
        drivers.sketch_id,
        drivers.sketch_name,
        drivers.feature_id,
        drivers.feature_name,
        drivers.depth.id,
        drivers.body_id,
        vertices,
        depth,
        width,
        height,
        DepthName=drivers.depth.attributes["freecad_path"],
        SketchDriverNames=(source_name, height_name),
    )
    return CornerIntent(
        recipe,
        joins,
        axes,
        length_rows,
        origin,
        (drivers.width.id, drivers.height.id, drivers.depth.id),
        body.name,
        drivers.support_plane_id,
    )
