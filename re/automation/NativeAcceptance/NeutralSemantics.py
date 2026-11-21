import math
import re


def Vector(value):
    return [value.x, value.y, value.z]


def World(point, frame):
    return [origin + point.x * x + point.y * y for origin, x, y in zip(Vector(frame.origin), Vector(frame.x_axis), Vector(frame.y_axis))]


def Scalar(value):
    factors = {"mm": 1, "cm": 10, "m": 1000, "in": 25.4, "ft": 304.8, "rad": 1, "deg": math.pi / 180, "": 1}
    if value is None or type(value.value) not in (int, float) or value.unit not in factors:
        return None
    result = value.value * factors[value.unit]
    return result if math.isfinite(result) else None


def Expression(source, dependencies):
    if source is None:
        return None
    if not dependencies and re.fullmatch(r"\s*[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\s*(?:mm|cm|m|in|ft|deg|rad)?\s*", source):
        return None
    return re.sub(r"\s+", "", source)


def ParameterNames(document, application):
    owners = {item.id: item.name for item in document.feature_timeline}
    names = {}
    for item in document.parameters:
        global_parameter = "equation:" in item.id
        names[item.id] = item.name if application == "fusion" or global_parameter else f"{item.name}@{owners.get(item.owner_id, item.owner_id)}"
    if len(set(names.values())) != len(names):
        raise ValueError("decoded parameter names are ambiguous")
    return names


def Entity(item, sketch, plane, native_names):
    from interchange.geometry.Models.GeometryCurves import ArcGeometry, CircleGeometry, LineGeometry, PointGeometry

    geometry = item.geometry
    if isinstance(geometry, PointGeometry):
        shape = {"point_mm": World(geometry.point, plane.transform)}
        kind = "point"
    elif isinstance(geometry, LineGeometry):
        shape = {"start_mm": World(geometry.start, plane.transform), "end_mm": World(geometry.end, plane.transform)}
        kind = "line"
    elif isinstance(geometry, CircleGeometry):
        shape = {"center_mm": World(geometry.center, plane.transform), "radius_mm": geometry.radius}
        kind = "circle"
    elif isinstance(geometry, ArcGeometry):
        from interchange.geometry.Models.VectorPlane import PlaneVector

        shape = {"center_mm": World(geometry.center, plane.transform), "radius_mm": geometry.radius, "start_mm": World(PlaneVector(geometry.center.x + geometry.radius * math.cos(geometry.start_angle), geometry.center.y + geometry.radius * math.sin(geometry.start_angle)), plane.transform), "end_mm": World(PlaneVector(geometry.center.x + geometry.radius * math.cos(geometry.end_angle), geometry.center.y + geometry.radius * math.sin(geometry.end_angle)), plane.transform)}
        kind = "arc"
    else:
        return None
    origin = item.attributes.get("native_origin_feature_id")
    owner = native_names.get(origin) if origin is not None else sketch.name
    return {"kind": kind, "owner": owner, "geometry": shape, "construction": item.construction, "fixed": item.fixed}


def Reference(ref, entities):
    entity = entities.get(ref.entity_id)
    if entity is None:
        return None
    if not ref.point:
        return entity
    key = {"start": "start_mm", "end": "end_mm", "center": "center_mm"}.get(ref.point)
    point = entity["geometry"].get(key)
    if point is None:
        return None
    return {"kind": "point", "owner": entity["owner"], "geometry": {"point_mm": point}, "construction": False, "fixed": False}


def SketchSemantics(sketch, document, names, gaps):
    planes = {item.id: item for item in document.support_planes}
    plane = planes.get(sketch.support_plane_id)
    if plane is None:
        gaps.append("sketch:" + sketch.name + ":support_plane")
        return {"name": sketch.name}
    features = {item.id: item.name for item in document.feature_timeline}
    native_names = {item.attributes.get("native_object_id"): item.name for item in document.feature_timeline}
    entities = {item.id: Entity(item, sketch, plane, native_names) for item in sketch.entities}
    for identity, value in entities.items():
        if value is None or value["owner"] is None:
            gaps.append("sketch:" + sketch.name + ":entity:" + identity)
    relations = []
    for item in sketch.constraints:
        operands = [Reference(ref, entities) for ref in item.references]
        if not operands or any(value is None for value in operands):
            gaps.append("sketch:" + sketch.name + ":constraint:" + item.id)
        relations.append({"kind": str(item.kind), "operands": operands, "parameter": names.get(item.parameter_id), "driving": item.driving, "suppressed": item.suppressed})
    support = None
    if plane.support_selection_id:
        selection = next((item for item in document.selections if item.id == plane.support_selection_id), None)
        producers = set() if selection is None else {part.entity_id for part in selection.path if part.entity_kind == "feature" and part.subelement.startswith(("face:", "end-face:"))}
        if len(producers) == 1:
            support = {"kind": "face", "feature": features.get(next(iter(producers)))}
            gaps.append("sketch:" + sketch.name + ":exact_support_face_identity")
    elif plane.offset_parameter_id is None:
        normal = Vector(plane.transform.z_axis)
        if sum(abs(value) > 1e-9 for value in normal) == 1 and all(abs(value) < 1e-9 for value in Vector(plane.transform.origin)):
            support = {"kind": "principal_plane", "normal": normal}
    if support is None:
        gaps.append("sketch:" + sketch.name + ":support_binding")
    if sketch.attributes.get("unresolved"):
        gaps.append("sketch:" + sketch.name + ":unresolved")
    return {"name": sketch.name, "frame": {"origin_mm": Vector(plane.transform.origin), "x_axis": Vector(plane.transform.x_axis), "y_axis": Vector(plane.transform.y_axis)}, "support": support, "entities": [item for item in entities.values() if item is not None], "constraints": relations}


def ExtrudeSemantics(item, document, names, gaps):
    from interchange.Features.FeatureDistExt import DistanceExtrude
    from interchange.Features.FeatureExtrude import ExtrudeFeature

    definition = item.definition
    parameters = {value.id: value for value in document.parameters}
    profile = next((value.name for value in document.sketches if value.id == item.sketch_id), None)
    common = {"name": item.name, "kind": "extrude", "operation": str(item.operation), "profile": profile}
    if profile is None:
        gaps.append("feature:" + item.name + ":profile_binding")
    if isinstance(definition, DistanceExtrude):
        length = parameters.get(definition.AlongParameterId)
        taper = parameters.get(definition.TaperParameterId)
        offset = parameters.get(definition.StartOffsetId)
        amount = Scalar(length.value) if length else None
        if definition.SideMode != "one_sided" or definition.AgainstParameterId or definition.SecondTaperId:
            gaps.append("feature:" + item.name + ":second_extent")
        return {**common, "length_mm": None if amount is None else abs(amount), "end_condition": "blind", "direction": [(-1 if amount is not None and amount < 0 else 1) * value for value in Vector(definition.Direction)], "side_mode": definition.SideMode, "taper_rad": Scalar(taper.value) if taper else 0.0, "start_offset_mm": Scalar(offset.value) if offset else 0.0, "bindings": {"length": names.get(definition.AlongParameterId), "taper": names.get(definition.TaperParameterId), "start_offset": names.get(definition.StartOffsetId)}}
    if not isinstance(definition, ExtrudeFeature):
        gaps.append("feature:" + item.name + ":definition:" + type(definition).__name__)
        return common
    if definition.symmetric or any(value is not None for value in (definition.second_length, definition.second_end_condition, definition.second_offset, definition.second_draft_angle)) or definition.up_to_reference or definition.second_up_to_reference or item.selection_ids:
        gaps.append("feature:" + item.name + ":extent_or_scope")
    if str(definition.end_condition) not in ("blind", "through_all"):
        gaps.append("feature:" + item.name + ":end_condition")
    owned = [parameters[key] for key in item.parameter_ids if key in parameters]
    lengths = [value for value in owned if value.value.unit in ("mm", "cm", "m", "in", "ft")]
    angles = [value for value in owned if value.value.unit in ("rad", "deg")]
    length_binding = names[lengths[0].id] if len(lengths) == 1 else None
    if definition.length is not None and length_binding is None:
        gaps.append("feature:" + item.name + ":length_binding")
    if definition.offset is not None or definition.draft_angle is not None or angles:
        gaps.append("feature:" + item.name + ":parameter_roles")
    direction = None if definition.direction is None else [(-1 if definition.reversed else 1) * value for value in Vector(definition.direction)]
    if direction is None:
        gaps.append("feature:" + item.name + ":direction")
    return {**common, "length_mm": Scalar(definition.length), "end_condition": str(definition.end_condition), "direction": direction, "side_mode": "one_sided", "taper_rad": Scalar(definition.draft_angle) if definition.draft_angle else 0.0, "start_offset_mm": Scalar(definition.offset) if definition.offset else 0.0, "bindings": {"length": length_binding, "taper": None, "start_offset": None}}


def NeutralSemantics(document, application):
    from interchange.Features.FeatureDistExt import DistanceExtrude
    from interchange.Features.FeatureExtrude import ExtrudeFeature

    gaps = []
    names = ParameterNames(document, application)
    owners = {item.id: item.name for item in document.feature_timeline}
    parameters = []
    for item in document.parameters:
        dependencies = [] if item.expression is None else [names.get(key) for key in item.expression.parameter_ids]
        if any(value is None for value in dependencies):
            gaps.append("parameter:" + names[item.id] + ":dependency_binding")
        parameters.append({"name": names[item.id], "owner": None if not item.owner_id or "equation:" in item.id else owners.get(item.owner_id), "role": "reference" if str(item.role) == "driven" else str(item.role), "expression": Expression(item.expression.source if item.expression else None, dependencies), "dependencies": sorted(dependencies, key=str)})
    features = []
    sketch_ids = {item.id for item in document.sketches}
    for item in document.feature_timeline:
        native_type = item.attributes.get("native_type", "")
        if item.sketch_id in sketch_ids and item.operation is None:
            row = {"name": item.name, "kind": "sketch"}
        elif isinstance(item.definition, (DistanceExtrude, ExtrudeFeature)):
            row = ExtrudeSemantics(item, document, names, gaps)
        elif application == "solidworks" and native_type == "RefPlane":
            plane = next((value for value in document.support_planes if value.attributes.get("native_object_id") == item.attributes.get("native_object_id")), None)
            if plane is None or not plane.attributes.get("principal"):
                gaps.append("feature:" + item.name + ":constructed_plane")
            continue
        elif application == "solidworks" and native_type in ("OriginProfileFeature", "HistoryFolder", "CommentsFolder", "FavoriteFolder", "SelectionSetFolder", "SensorFolder", "DetailCabinet", "MaterialFolder", "SolidBodyFolder", "SurfaceBodyFolder", "FtrFolder", "EqnFolder", "Attribute", "ICEFolder", "DocsFolder", "NotesAreaFtrFolder", "EnvFolder", "AmbientLight", "DirectionLight", "InkMarkupFolder", "AnnotationView", "NotesArea"):
            continue
        else:
            gaps.append("feature:" + item.name + ":definition:" + type(item.definition).__name__)
            row = {"name": item.name, "kind": "unsupported"}
        features.append(row)
    semantic_names = {item["name"] for item in features}
    if len(semantic_names) != len(features):
        raise ValueError("decoded semantic feature names are ambiguous")
    for row in features:
        feature = next(item for item in document.feature_timeline if item.name == row["name"])
        row["dependencies"] = sorted(owners[key] for key in feature.input_feature_ids if owners.get(key) in semantic_names)
    if document.assembly is not None:
        gaps.append("assembly")
    if len(document.configurations) > 1 or any(item.configuration_states for item in document.feature_timeline):
        gaps.append("configuration_states")
    return {"schema": 1, "features": features, "sketches": [SketchSemantics(item, document, names, gaps) for item in document.sketches], "parameters": parameters, "gaps": gaps}
