from math import isfinite

from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.geometry.Models.GeometryCurves import (
    CircleGeometry,
    LineGeometry,
    PointGeometry,
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def vector(value):
    return (value.x, value.y, value.z)


def frame(plane):
    value = plane.transform
    return {
        "origin": vector(value.origin),
        "u": vector(value.x_axis),
        "v": vector(value.y_axis),
        "normal": vector(value.z_axis),
    }


def rectangle(sketch, scale):
    require(
        not sketch.suppressed and not sketch.parameter_ids,
        "stock sketch state is not admitted",
    )
    require(
        len(sketch.entities) == 4, "stock must retain exactly four actual line owners"
    )
    require(
        len(sketch.closed_profile_entity_ids) == 1,
        "stock needs its actual closed contour",
    )
    by_id = {entity.id: entity for entity in sketch.entities}
    ring = sketch.closed_profile_entity_ids[0]
    require(
        len(ring) == 4 and set(ring) == set(by_id),
        "stock contour must cover every actual line once",
    )
    segments = []
    expected = {}
    for entity in sketch.entities:
        geometry = entity.geometry
        require(
            type(geometry) is LineGeometry and entity.kind == "line",
            "stock contains a nonline owner",
        )
        require(
            not entity.construction and not entity.fixed,
            "stock line carries unrepresented construction or fixation",
        )
        start = (geometry.start.x * scale, geometry.start.y * scale)
        end = (geometry.end.x * scale, geometry.end.y * scale)
        require(
            start != end and all(isfinite(item) for item in (*start, *end)),
            "stock edge is degenerate",
        )
        require(
            start[0] == end[0] or start[1] == end[1], "stock edge is not axis aligned"
        )
        expected[entity.id] = "vertical" if start[0] == end[0] else "horizontal"
        segments.append((start, end))
    actual = {}
    for relation in sketch.constraints:
        require(len(relation.references) == 1, "stock relation has ambiguous incidence")
        reference = relation.references[0]
        require(
            not reference.point and reference.entity_id not in actual,
            "stock relation duplicates or subselects a line",
        )
        require(
            relation.driving
            and not relation.suppressed
            and relation.parameter_id is None,
            "stock relation has unrepresented parameter state",
        )
        actual[reference.entity_id] = relation.kind
    require(actual == expected, "stock must preserve all four actual axis relations")
    points = {point for segment in segments for point in segment}
    xs, ys = sorted({point[0] for point in points}), sorted(
        {point[1] for point in points}
    )
    require(
        len(xs) == len(ys) == 2 and points == {(x, y) for x in xs for y in ys},
        "stock is not a complete rectangle",
    )
    expected_edges = {
        frozenset((a, b))
        for a, b in zip(
            ((xs[0], ys[0]), (xs[1], ys[0]), (xs[1], ys[1]), (xs[0], ys[1])),
            ((xs[1], ys[0]), (xs[1], ys[1]), (xs[0], ys[1]), (xs[0], ys[0])),
            strict=True,
        )
    }
    require(
        {frozenset(segment) for segment in segments} == expected_edges,
        "stock contour does not bound the actual rectangle",
    )
    return {
        "minimum": (xs[0], ys[0]),
        "maximum": (xs[1], ys[1]),
        "source_line_ids": tuple(by_id),
        "source_profile_order": ring,
    }


def circle(sketch, scale, document):
    require(
        not sketch.suppressed and not sketch.parameter_ids and not sketch.constraints,
        "through profile has unrepresented driving constraints",
    )
    circles = [
        entity for entity in sketch.entities if type(entity.geometry) is CircleGeometry
    ]
    points = [
        entity for entity in sketch.entities if type(entity.geometry) is PointGeometry
    ]
    require(
        len(circles) == len(points) == 1 and len(sketch.entities) == 2,
        "through profile must retain its actual circle and centre point",
    )
    arc, center = circles[0], points[0]
    require(
        not any(entity.construction or entity.fixed for entity in sketch.entities),
        "free circle has authored construction or fixation",
    )
    require(
        sketch.closed_profile_entity_ids == ((arc.id,),),
        "circle profile ownership differs",
    )
    require(
        center.geometry.point == arc.geometry.center,
        "centre point is independent of the actual circle",
    )
    report = document.metadata.get("solidworks.typed_resolved_semantics", {})
    native_id = sketch.attributes.get("native_object_id")
    require(
        native_id in report.get("free_circle_profiles", ()),
        "actual typed free-circle ownership is not proved",
    )
    value = arc.geometry
    require(isfinite(value.radius) and value.radius > 0, "circle radius is invalid")
    return {
        "center": (value.center.x * scale, value.center.y * scale),
        "radius": value.radius * scale,
        "circle_id": arc.id,
        "center_point_id": center.id,
        "center_point_binding": "qualified_typed_circle_owner",
    }


def axis_references(document, operations, sketches, plane):
    ids = set()
    result = []
    for operation, sketch in zip(operations, sketches, strict=True):
        candidates = [
            value
            for value in document.selections
            if value.query.get("topology_role") == "direction_axis"
            and value.query.get("native_owner_id")
            == operation.attributes.get("native_object_id")
        ]
        require(
            len(candidates) == 1,
            "operation lacks its unique native direction-axis projection",
        )
        value = candidates[0]
        require(
            len(value.path) == 1
            and value.path[0].entity_kind == "native"
            and value.path[0].entity_id == sketch.name
            and value.path[0].subelement == "N_Axis",
            "direction axis is not its actual sketch normal",
        )
        require(
            value.query.get("native_target_id")
            == sketch.attributes.get("native_object_id"),
            "direction axis targets a foreign sketch",
        )
        require(
            value.point is None and not value.attributes,
            "direction-axis selection has unsupported extensions",
        )
        ids.add(value.id)
        result.append(
            {
                "source_selection_id": value.id,
                "owner_feature_id": operation.id,
                "target_sketch_id": sketch.id,
                "principal_plane_id": plane.id,
                "normal": vector(plane.transform.z_axis),
            }
        )
    return ids, result


def selected_stock(document, boss, cut, body):
    require(
        len(cut.selection_ids) == 1, "cut needs exactly one explicit stock selection"
    )
    matches = [
        value for value in document.selections if value.id == cut.selection_ids[0]
    ]
    require(len(matches) == 1, "cut selected-stock identity is missing or duplicated")
    selection = matches[0]
    require(len(selection.path) == 1, "selected-stock path is ambiguous")
    element = selection.path[0]
    require(
        (element.entity_kind, element.entity_id, element.subelement)
        == ("feature", boss.id, "body"),
        "selected-stock path must name the actual producer and body role",
    )
    require(
        not selection.query and selection.point is None and not selection.attributes,
        "selected-stock extension is unrepresented",
    )
    require(
        body.final_feature_id == cut.id,
        "selected stock result does not bind the actual final cut",
    )
    evidence = document.metadata.get("solidworks.typed_resolved_semantics", {}).get(
        "cut_body_dependency", {}
    )
    require(
        evidence.get("feature_scope_code") == 1
        and evidence.get("binding") == "saved_configuration_atom_alias",
        "source is not the qualified saved selected-stock branch",
    )
    require(
        evidence.get("producer_feature_id") == boss.attributes.get("native_object_id")
        and evidence.get("consumer_feature_id")
        == cut.attributes.get("native_object_id"),
        "selected-stock evidence has a stale owner",
    )
    return {
        "selection_id": selection.id,
        "producer_id": boss.id,
        "result_body_id": body.id,
        "mode": "explicit_selected_stock",
        "continuous_automatic_selection": "not_encoded_or_claimed",
    }


def read_shape(document):
    document.assert_valid()
    require(
        document.assembly is None and document.DrawingValue is None,
        "source is not an ordinary part",
    )
    require(
        len(document.bodies) == len(document.configurations) == 1
        and len(document.sketches) == 2
        and len(document.parameters) == 1,
        "source has additional body configuration sketch or parameter owners",
    )
    require(
        not document.materials and not document.meshes and not document.diagnostics,
        "source has unsupported material mesh or unresolved semantics",
    )
    config = document.configurations[0]
    require(
        config.active
        and config.parent_id is None
        and not config.overrides
        and not config.suppressed_feature_ids,
        "configuration is not one independent active variant",
    )
    scale = {"mm": 0.001, "m": 1.0, "in": 0.0254}.get(str(document.units))
    require(scale is not None, "source length units are unsupported")
    operations = tuple(
        value
        for value in document.feature_timeline
        if type(value.definition) is ExtrudeFeature
    )
    require(
        len(operations) == 2, "source must retain exactly its stock and cut operations"
    )
    boss, cut = operations
    require(
        boss.operation == "join" and cut.operation == "cut",
        "source operation order differs from ordinary stock then cut",
    )
    require(
        boss.order < cut.order
        and not any(
            value.suppressed or value.configuration_states for value in operations
        ),
        "operation state is not admitted",
    )
    sketches = {value.id: value for value in document.sketches}
    stock_sketch, cut_sketch = sketches.get(boss.sketch_id), sketches.get(cut.sketch_id)
    require(
        stock_sketch is not None
        and cut_sketch is not None
        and stock_sketch is not cut_sketch,
        "operation profile ownership is ambiguous",
    )
    require(
        stock_sketch.support_plane_id == cut_sketch.support_plane_id,
        "profiles do not share their actual support",
    )
    planes = {value.id: value for value in document.support_planes}
    plane = planes.get(stock_sketch.support_plane_id)
    require(
        plane is not None and len(planes) == 3,
        "source lacks its three actual principal datums",
    )
    from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadPrincAxis import (
        ReadPrincAxis,
    )

    axis = ReadPrincAxis(plane.transform)
    require(
        {ReadPrincAxis(value.transform) for value in planes.values()}
        == {"x", "y", "z"},
        "principal datum ownership is incomplete",
    )
    boss_def, cut_def = boss.definition, cut.definition
    for definition in (boss_def, cut_def):
        require(
            all(
                getattr(definition, key) is None
                for key in (
                    "offset",
                    "second_offset",
                    "draft_angle",
                    "second_draft_angle",
                )
            )
            and not definition.up_to_reference
            and not definition.second_up_to_reference,
            "extrusion has unsupported offset draft or target semantics",
        )
        require(
            definition.direction is None
            or vector(definition.direction) == vector(plane.transform.z_axis),
            "extrusion direction does not follow the actual support normal",
        )
    require(
        boss_def.end_condition == "mid_plane"
        and boss_def.symmetric
        and not boss_def.reversed
        and boss_def.second_length is None
        and boss_def.second_end_condition is None,
        "stock is not the qualified forward mid-plane prism",
    )
    driver = document.parameters[0]
    require(
        driver.owner_id == boss.id
        and driver.name == "D1"
        and driver.role == "driving"
        and driver.expression is None
        and driver.value == boss_def.length
        and boss.parameter_ids == (driver.id,),
        "stock driver is not its actual total depth",
    )
    require(
        str(driver.value.unit) == str(document.units) and driver.value.kind == "length",
        "stock parameter units differ from actual document units",
    )
    require(
        cut_def.end_condition == "through_all"
        and cut_def.second_end_condition in (None, "through_all")
        and cut_def.length is None
        and cut_def.second_length is None
        and not cut_def.symmetric
        and not cut.parameter_ids,
        "cut carries unused distances or a different termination",
    )
    profile_steps = {
        value.sketch_id: value
        for value in document.feature_timeline
        if value.sketch_id in sketches and value not in operations
    }
    require(
        set(profile_steps) == set(sketches),
        "source lacks its actual profile history nodes",
    )
    stock_step, cut_step = profile_steps[stock_sketch.id], profile_steps[cut_sketch.id]
    require(
        boss.input_feature_ids == (stock_step.id,)
        and cut.input_feature_ids == (boss.id, cut_step.id),
        "operation dependencies omit or change the actual profile and producer",
    )
    axis_ids, axes = axis_references(
        document, operations, (stock_sketch, cut_sketch), plane
    )
    scope = selected_stock(document, boss, cut, document.bodies[0])
    require(
        set(value.id for value in document.selections)
        == axis_ids | {scope["selection_id"]},
        "source has unrepresented additional selections",
    )
    rect = rectangle(stock_sketch, scale)
    tool = circle(cut_sketch, scale, document)
    require(
        all(
            rect["minimum"][index]
            < tool["center"][index] - tool["radius"]
            < tool["center"][index] + tool["radius"]
            < rect["maximum"][index]
            for index in (0, 1)
        ),
        "circle is not fully enclosed by the actual stock",
    )
    return {
        "units": "m",
        "support_axis": axis,
        "support": frame(plane),
        "stock": rect,
        "tool": tool,
        "depth": driver.value.value * scale,
        "driver_id": driver.id,
        "stock_feature_id": boss.id,
        "cut_feature_id": cut.id,
        "stock_sketch_id": stock_sketch.id,
        "cut_sketch_id": cut_sketch.id,
        "source_configuration_id": config.id,
        "configuration_name": config.name,
        "cut_reversed": cut_def.reversed,
        "second_through_all": cut_def.second_end_condition == "through_all",
        "axis_references": axes,
        "scope": scope,
    }
