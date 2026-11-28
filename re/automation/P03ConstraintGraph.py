"""Project the exact saved P03 constraint graph into existing logical Boss input."""

from dataclasses import replace

from PairedCaptureIntake import require
from RectanglePairBoss import find_boss
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureDistExt import DistanceExtrude
from interchange.Features.FeatureKinds import NativeFeature
from interchange.geometry.Models.GeometryCurves import LineGeometry, PointGeometry
from interchange.geometry.Models.Sketch import ConstraintRef
from interchange.Records.RecordSource import CadSource


def same_owner(sketch, owner):
    left, right = sketch.provenance, owner.provenance
    require(
        left is not None
        and right is not None
        and left.adapter == right.adapter == "solidworks.sldprt"
        and left.native_id
        and left.native_id == right.native_id,
        "P03 sketch must have one matching typed native owner",
    )
    (a,) = [span for span in left.spans if span.record_kind == "sketch-record"]
    (b,) = [span for span in right.spans if span.record_kind == "feature-record"]
    (support,) = [
        span for span in left.spans if span.record_kind == "sketch-support-reference"
    ]
    require(
        support.stream == a.stream
        and support.length == 4
        and a.offset <= support.offset <= a.offset + a.length - support.length,
        "P03 support pointer must lie within its owning sketch",
    )
    require(
        a.stream == b.stream == "Contents/Config-0-ResolvedFeatures"
        and a.offset == b.offset
        and a.length == b.length > 0,
        "P03 sketch owner span differs from the declared sketch span",
    )
    return [a.stream, a.offset, a.length]


def selected_graph(document):
    (sketch,) = document.sketches
    boss, loop = find_boss(document, sketch)
    (owner,) = [
        feature
        for feature in document.feature_timeline
        if feature.id in boss.input_feature_ids
    ]
    require(
        owner.kind == "reference"
        and owner.operation is None
        and not owner.suppressed
        and owner.sketch_id == sketch.id
        and boss.input_feature_ids == (owner.id,)
        and isinstance(owner.definition, NativeFeature)
        and owner.definition.object_data.get("native_class") == "moProfileFeature_c"
        and boss.order > owner.order,
        "P03 Boss does not select the typed sketch owner",
    )
    span = same_owner(sketch, owner)
    (plane,) = [
        value
        for value in document.support_planes
        if value.id == sketch.support_plane_id
    ]
    (datum,) = [
        feature
        for feature in document.feature_timeline
        if feature.id in owner.input_feature_ids
    ]
    require(
        owner.input_feature_ids == (datum.id,)
        and plane.name == "Front Plane"
        and datum.provenance.native_id == plane.provenance.native_id,
        "P03 saved Front support does not belong to the selected sketch",
    )
    return sketch, owner, boss, plane, loop, span


def perimeter(document, sketch, loop):
    entities = {entity.id: entity for entity in sketch.entities}
    lines = tuple(entities[identity] for identity in loop)
    points = tuple(entity for entity in sketch.entities if entity.id not in loop)
    (origin,) = [entity for entity in points if entity.fixed]
    aliases = tuple(entity for entity in points if entity is not origin)
    require(
        len(points) == 5
        and all(
            isinstance(line.geometry, LineGeometry)
            and not line.fixed
            and not line.construction
            for line in lines
        )
        and all(
            isinstance(point.geometry, PointGeometry) and point.construction
            for point in points
        )
        and origin.geometry.point == lines[0].geometry.start
        and origin.geometry.point.x == origin.geometry.point.y == 0.0,
        "P03 needs four ordered lines, four corner aliases and a separate fixed Origin",
    )
    origin_id = origin.attributes.get("native_origin_feature_id")
    origins = [
        feature
        for feature in document.feature_timeline
        if feature.name == "Origin"
        and feature.provenance is not None
        and feature.provenance.native_id == str(origin_id)
    ]
    require(
        len(origins) == 1 and origin_id is not None,
        "P03 fixed point is not bound to the model Origin",
    )
    alias_ids = []
    for previous, following in zip(lines[-1:] + lines[:-1], lines, strict=True):
        start = following.geometry.start
        native_points = set(previous.attributes["native_point_indices"]) & set(
            following.attributes["native_point_indices"]
        )
        matches = [
            point
            for point in aliases
            if point.geometry.point == start
            and {point.attributes["native_point_id"][0]} == native_points
        ]
        require(
            previous.geometry.end == start and len(matches) == 1,
            "P03 endpoint joins must identify one shared native corner",
        )
        alias_ids.append(matches[0].id)
    require(
        len(set(alias_ids)) == 4,
        "P03 corners do not own four distinct native point aliases",
    )
    return lines, origin, alias_ids


def ordered_rules(sketch, loop, origin, parameters):
    actual = tuple(
        (rule.kind, rule.references, rule.parameter_id) for rule in sketch.constraints
    )
    axes = tuple(
        ("horizontal" if slot % 2 == 0 else "vertical", (ConstraintRef(edge),), None)
        for slot, edge in enumerate(loop)
    )
    width = (
        "distance",
        (ConstraintRef(loop[0], "start"), ConstraintRef(loop[0], "end")),
        parameters["width_mm"].id,
    )
    height = (
        "distance",
        (ConstraintRef(loop[3], "end"), ConstraintRef(loop[3], "start")),
        parameters["height_mm"].id,
    )
    joins = tuple(
        (
            "coincident",
            (ConstraintRef(edge, "end"), ConstraintRef(next_edge, "start")),
            None,
        )
        for edge, next_edge in zip(loop, loop[1:] + loop[:1], strict=True)
    )
    anchor = (
        "coincident",
        (ConstraintRef(origin.id), ConstraintRef(loop[0], "start")),
        None,
    )
    require(
        actual == (*axes, height, width, *joins, anchor),
        "P03 ordered constraint endpoints differ from the saved anchored sides",
    )
    saved = tuple(
        rule for rule in sketch.constraints if not rule.attributes.get("inferred")
    )
    inferred = tuple(
        rule for rule in sketch.constraints if rule.attributes.get("inferred")
    )
    require(
        len(saved) == 7
        and all(
            rule.driving and not rule.suppressed and rule.provenance is not None
            for rule in saved
        )
        and len(inferred) == 4
        and all(
            rule.attributes == {"inferred": True} and rule.provenance is None
            for rule in inferred
        ),
        "P03 must distinguish saved solver relations from inferred shared corners",
    )
    return saved, inferred


def clean(record, **updates):
    return replace(record, attributes={}, provenance=None, **updates)


def project_source(document):
    sketch, owner, boss, plane, loop, span = selected_graph(document)
    lines, origin, aliases = perimeter(document, sketch, loop)
    parameters = {parameter.name: parameter for parameter in document.parameters}
    require(
        set(parameters) == {"width_mm", "height_mm", "depth_mm"},
        "P03 has different driving lengths",
    )
    saved, inferred = ordered_rules(sketch, loop, origin, parameters)
    depth = parameters["depth_mm"]
    (body,) = document.bodies
    (config,) = [value for value in document.configurations if value.active]
    require(
        body.final_feature_id == boss.id
        and boss.operation == "join"
        and tuple(value.id for value in document.feature_timeline if value.operation)
        == (boss.id,)
        and boss.definition.direction == plane.transform.z_axis
        and boss.definition.length == depth.value
        and depth.value.value > 0
        and not boss.definition.reversed
        and all(
            parameters[name].owner_id == owner.id for name in ("width_mm", "height_mm")
        )
        and depth.owner_id == boss.id,
        "P03 body and driving dimensions do not belong to the first positive blind Boss",
    )
    projected = CadDocument(
        source=CadSource("kit.neutral", "", ""),
        configurations=(replace(config, attributes={}),),
        parameters=tuple(clean(parameter) for parameter in document.parameters),
        support_planes=(clean(plane),),
        sketches=(
            clean(
                sketch,
                entities=tuple(clean(entity) for entity in (*lines, origin)),
                constraints=tuple(
                    replace(rule, provenance=None) if rule in inferred else clean(rule)
                    for rule in sketch.constraints
                ),
            ),
        ),
        selections=(),
        feature_timeline=(
            clean(owner, input_feature_ids=(), definition=None),
            clean(
                boss,
                operation="create",
                definition=DistanceExtrude(depth.id, plane.transform.z_axis),
            ),
        ),
        bodies=(clean(body, topology=type(body.topology)()),),
        units=document.units,
    )
    evidence = {
        "source_sha256": document.source.sha256,
        "owner": owner.id,
        "sketch": sketch.id,
        "owner_span": span,
        "support": plane.id,
        "origin": origin.id,
        "saved_relations": [rule.id for rule in saved],
        "shared_corner_aliases": aliases,
        "inferred_join_ids": [rule.id for rule in inferred],
        "source_operation": str(boss.operation),
        "original_native_features_outside_projection": [
            value.id
            for value in document.feature_timeline
            if isinstance(value.definition, NativeFeature)
        ],
    }
    return projected, evidence
