import re


def PointMm(point):
    return [value * 10 for value in point.asArray()]


def ObjectKind(value):
    return value.objectType.rsplit("::", 1)[-1]


def Descriptor(entity):
    kind = ObjectKind(entity)
    owner = entity.parentSketch
    if kind == "SketchPoint":
        geometry = {"point_mm": PointMm(entity.worldGeometry)}
        construction = entity == owner.originPoint
        shape = "point"
    elif kind == "SketchLine":
        geometry = {"start_mm": PointMm(entity.startSketchPoint.worldGeometry), "end_mm": PointMm(entity.endSketchPoint.worldGeometry)}
        construction = entity.isConstruction
        shape = "line"
    elif kind in ("SketchCircle", "SketchArc"):
        geometry = {"center_mm": PointMm(entity.centerSketchPoint.worldGeometry), "radius_mm": entity.radius * 10}
        if kind == "SketchArc":
            geometry.update(start_mm=PointMm(entity.startSketchPoint.worldGeometry), end_mm=PointMm(entity.endSketchPoint.worldGeometry))
        construction = entity.isConstruction
        shape = "circle" if kind == "SketchCircle" else "arc"
    else:
        raise ValueError("unsupported sketch entity " + kind)
    if (entity.isReference or entity.isLinked) and entity != owner.originPoint:
        raise ValueError("projected sketch geometry needs a proven source reference binding")
    return {"kind": shape, "geometry": geometry, "construction": bool(construction), "fixed": bool(entity.isFixed), "owner": owner.name}


def Constraint(relation):
    kind = ObjectKind(relation)
    if kind in ("HorizontalConstraint", "VerticalConstraint"):
        name = "horizontal" if kind == "HorizontalConstraint" else "vertical"
        operands = [relation.line]
    elif kind == "CoincidentConstraint":
        name = "coincident"
        operands = [relation.point, relation.entity]
    elif kind in ("ParallelConstraint", "CollinearConstraint"):
        name = {"ParallelConstraint": "parallel", "CollinearConstraint": "collinear"}[kind]
        operands = [relation.lineOne, relation.lineTwo]
    elif kind == "PerpendicularConstraint":
        name = "perpendicular"
        operands = [relation.line, relation.curve]
    elif kind in ("TangentConstraint", "EqualConstraint"):
        name = {"TangentConstraint": "tangent", "EqualConstraint": "equal"}[kind]
        operands = [relation.curveOne, relation.curveTwo]
    elif kind == "ConcentricConstraint":
        name = "concentric"
        operands = [relation.entityOne, relation.entityTwo]
    elif kind == "MidPointConstraint":
        name = "midpoint"
        operands = [relation.point, relation.midPointCurve]
    else:
        raise ValueError("unsupported sketch constraint " + kind)
    return {"kind": name, "operands": [Descriptor(item) for item in operands], "parameter": None, "driving": True, "suppressed": False}


def Dimension(dimension):
    import adsk.fusion

    kind = ObjectKind(dimension)
    if kind == "SketchLinearDimension":
        name = {
            adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation: "distance_x",
            adsk.fusion.DimensionOrientations.VerticalDimensionOrientation: "distance_y",
            adsk.fusion.DimensionOrientations.AlignedDimensionOrientation: "distance",
        }.get(dimension.orientation)
        if name is None:
            raise ValueError("unknown linear dimension orientation")
        operands = [dimension.entityOne, dimension.entityTwo]
    elif kind == "SketchAngularDimension":
        name = "angle"
        operands = [dimension.lineOne, dimension.lineTwo]
    elif kind in ("SketchRadialDimension", "SketchDiameterDimension"):
        name = "radius" if kind == "SketchRadialDimension" else "diameter"
        operands = [dimension.entity]
    else:
        raise ValueError("unsupported sketch dimension " + kind)
    parameter = dimension.parameter
    if parameter is None:
        raise ValueError("nonparametric sketch dimension")
    return {"kind": name, "operands": [Descriptor(item) for item in operands], "parameter": parameter.name, "driving": bool(dimension.isDriving), "suppressed": False}


def FaceProducer(face, design, before):
    matches = []
    for index in range(before):
        timeline = design.timeline.item(index)
        feature = timeline.entity
        if ObjectKind(feature) == "Sketch" or not hasattr(feature, "faces") or timeline.isSuppressed:
            continue
        if any(candidate == face for candidate in feature.faces):
            matches.append(feature.name)
    if len(matches) != 1:
        raise ValueError("support face producer is absent or ambiguous")
    return matches[0]


def Support(sketch, design):
    marker = design.timeline.markerPosition
    try:
        if not sketch.timelineObject.rollTo(False):
            raise ValueError("could not roll timeline after sketch to inspect its support")
        plane = sketch.referencePlane
        kind = ObjectKind(plane)
        if kind == "ConstructionPlane":
            if plane.isDeletable or plane.isDerived:
                raise ValueError("authored construction plane needs its own semantic definition")
            return {"kind": "principal_plane", "normal": list(plane.geometry.normal.asArray())}
        if kind == "BRepFace":
            return {"kind": "face", "feature": FaceProducer(plane, design, sketch.timelineObject.index)}
        raise ValueError("unsupported sketch support " + kind)
    finally:
        design.timeline.markerPosition = marker


def SketchSemantics(sketch, design, gaps):
    label = "sketch:" + sketch.name
    if not sketch.isParametric or sketch.isDerived or sketch.baseOrFormFeature is not None:
        gaps.append(label + ":nonparametric_or_derived")
    if sketch.sketchTexts.count:
        gaps.append(label + ":sketch_text")
    entities = []
    constraints = []
    for index, entity in enumerate([*sketch.sketchPoints, *sketch.sketchCurves]):
        try:
            entities.append(Descriptor(entity))
        except (AttributeError, RuntimeError, ValueError) as error:
            gaps.append(f"{label}:entity:{index}:{error}")
    for index, relation in enumerate([*sketch.geometricConstraints, *sketch.sketchDimensions]):
        try:
            constraints.append(Dimension(relation) if ObjectKind(relation).startswith("Sketch") else Constraint(relation))
        except (AttributeError, RuntimeError, ValueError) as error:
            gaps.append(f"{label}:constraint:{index}:{error}")
    try:
        support = Support(sketch, design)
    except (AttributeError, RuntimeError, ValueError) as error:
        support = None
        gaps.append(f"{label}:support:{error}")
    return {"name": sketch.name, "frame": {"origin_mm": PointMm(sketch.origin), "x_axis": list(sketch.xDirection.asArray()), "y_axis": list(sketch.yDirection.asArray())}, "support": support, "entities": entities, "constraints": constraints}


def BodyProducer(body, design, before):
    matches = []
    for index in range(before):
        timeline = design.timeline.item(index)
        feature = timeline.entity
        if not hasattr(feature, "bodies") or timeline.isSuppressed:
            continue
        if any(candidate == body for candidate in feature.bodies):
            matches.append(feature.name)
    if not matches:
        raise ValueError("participant body has no earlier feature producer")
    return matches[-1]


def ExtrudeSemantics(feature, design):
    import adsk.fusion

    if not feature.isParametric or not feature.isSolid or feature.isThinExtrude or feature.hasTwoExtents or feature.symmetricExtent is not None:
        raise ValueError("extrusion needs a solid parametric single sided nonthin extent")
    marker = design.timeline.markerPosition
    try:
        if not feature.timelineObject.rollTo(True):
            raise ValueError("could not roll timeline before extrusion to inspect its profile")
        profile = feature.profile
        if ObjectKind(profile) != "Profile":
            raise ValueError("extrusion profile needs one authored sketch profile")
        sketch = profile.parentSketch
        if sketch.profiles.count != 1:
            raise ValueError("multiple sketch profiles need exact selected loop bindings")
        operation = {
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation: "create",
            adsk.fusion.FeatureOperations.JoinFeatureOperation: "join",
            adsk.fusion.FeatureOperations.CutFeatureOperation: "cut",
            adsk.fusion.FeatureOperations.IntersectFeatureOperation: "intersect",
        }.get(feature.operation)
        if operation is None:
            raise ValueError("unknown extrusion operation")
        extent = feature.extentOne
        extent_kind = ObjectKind(extent)
        length_binding = None
        if extent_kind == "DistanceExtentDefinition":
            distance = extent.distance
            length = abs(distance.value * 10)
            sign = -1 if distance.value < 0 else 1
            length_binding = distance.name
            end = "blind"
        elif extent_kind == "ThroughAllExtentDefinition":
            length = None
            sign = 1 if extent.isPositiveDirection else -1
            end = "through_all"
        else:
            raise ValueError("unsupported extrusion extent " + extent_kind)
        start = feature.startExtent
        start_kind = ObjectKind(start)
        offset_binding = None
        if start_kind == "ProfilePlaneStartDefinition":
            offset = 0.0
        elif start_kind == "OffsetStartDefinition":
            offset = start.offset.value * 10
            offset_binding = start.offset.name
        else:
            raise ValueError("unsupported extrusion start " + start_kind)
        normal = sketch.xDirection.crossProduct(sketch.yDirection)
        if not normal.normalize():
            raise ValueError("extrusion profile has no unit normal")
        dependencies = [sketch.name]
        if operation in ("cut", "intersect"):
            participants = list(feature.participantBodies)
            if not participants:
                raise ValueError("cut or intersection has no participant bodies")
            dependencies.extend(BodyProducer(body, design, feature.timelineObject.index) for body in participants)
        elif operation == "join":
            raise ValueError("join requires independently resolved participant body bindings")
        taper = feature.taperAngleOne
        return {"name": feature.name, "kind": "extrude", "operation": operation, "profile": sketch.name, "length_mm": length, "end_condition": end, "direction": [sign * value for value in normal.asArray()], "taper_rad": taper.value, "start_offset_mm": offset, "side_mode": "one_sided", "bindings": {"length": length_binding, "taper": taper.name, "start_offset": offset_binding}, "dependencies": sorted(set(dependencies))}
    finally:
        design.timeline.markerPosition = marker


def ParameterSemantics(parameter):
    dependencies = sorted(item.name for item in parameter.dependencyParameters)
    owner = None
    role = "derived" if ObjectKind(parameter) == "DerivedParameter" else "driving"
    if ObjectKind(parameter) == "ModelParameter":
        creator = parameter.createdBy
        if creator is None:
            raise ValueError("model parameter has no owning feature or dimension")
        if hasattr(creator, "parentSketch"):
            owner = creator.parentSketch.name
            if hasattr(creator, "isDriving") and not creator.isDriving:
                role = "reference"
        elif hasattr(creator, "name"):
            owner = creator.name
        else:
            raise ValueError("model parameter creator has no semantic identity")
    expression = parameter.expression
    if not dependencies and re.fullmatch(r"\s*[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\s*(?:mm|cm|m|in|ft|deg|rad)?\s*", expression):
        expression = None
    elif expression is not None:
        expression = re.sub(r"\s+", "", expression)
    return {"name": parameter.name, "owner": owner, "role": role, "expression": expression, "dependencies": dependencies}


def MeasureSemantics(design):
    import adsk.fusion

    gaps = []
    features = []
    sketches = []
    parameters = []
    if design.designType != adsk.fusion.DesignTypes.ParametricDesignType:
        gaps.append("design:nonparametric")
    for index, item in enumerate(design.timeline):
        entity = item.entity
        kind = ObjectKind(entity)
        try:
            if item.isSuppressed:
                raise ValueError("suppressed feature needs configuration specific definition inspection")
            if kind == "Sketch":
                sketch = SketchSemantics(entity, design, gaps)
                support = sketch["support"]
                features.append({"name": item.name, "kind": "sketch", "dependencies": [support["feature"]] if support is not None and support["kind"] == "face" else []})
                sketches.append(sketch)
            elif kind == "ExtrudeFeature":
                features.append(ExtrudeSemantics(entity, design))
            else:
                raise ValueError("unsupported authored feature " + kind)
        except (AttributeError, RuntimeError, ValueError) as error:
            gaps.append(f"feature:{index}:{item.name}:{error}")
    for parameter in design.allParameters:
        try:
            parameters.append(ParameterSemantics(parameter))
        except (AttributeError, RuntimeError, ValueError) as error:
            gaps.append(f"parameter:{parameter.name}:{error}")
    return {"schema": 1, "features": features, "sketches": sketches, "parameters": parameters, "gaps": gaps}
