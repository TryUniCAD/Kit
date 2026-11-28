import math
import re

from NativeAcceptance.SolidWorksCom import Member


def Bounded(values, label, limit=16384):
    result = list(values or ())
    if len(result) > limit:
        raise ValueError(label + " exceeds its measurement limit")
    return result


def World(transform, point):
    data = tuple(float(value) for value in transform.ArrayData)
    if len(data) != 16 or any(not math.isfinite(value) for value in data):
        raise ValueError("native sketch transform has invalid affine data")
    if data[12] != 1.0:
        raise ValueError("native sketch transform is not unit scale")
    return [
        (math.fsum(point[axis] * data[3 * axis + column] for axis in range(3)) + data[9 + column])
        * 1000
        for column in range(3)
    ]


def Frame(transform):
    origin = World(transform, (0, 0, 0))
    x_point = World(transform, (1, 0, 0))
    y_point = World(transform, (0, 1, 0))
    return {"origin_mm": origin, "x_axis": [(value - base) / 1000 for value, base in zip(x_point, origin)], "y_axis": [(value - base) / 1000 for value, base in zip(y_point, origin)]}


def Normal(frame):
    x, y = frame["x_axis"], frame["y_axis"]
    result = [x[1] * y[2] - x[2] * y[1], x[2] * y[0] - x[0] * y[2], x[0] * y[1] - x[1] * y[0]]
    if not math.isclose(math.hypot(*result), 1, abs_tol=1e-9):
        raise ValueError("native sketch frame is not orthonormal")
    return result


def Owner(app, sketch, owners):
    matches = [(name, value["sketch"], value["origin"]) for name, value in owners.items() if sketch is not None and int(app.IsSame(sketch, value["sketch"])) == 1]
    if len(matches) != 1:
        raise ValueError("native entity sketch owner is unavailable or ambiguous")
    return matches[0]


def Entity(app, item, owners):
    if item is None:
        raise ValueError("native constraint has a null operand")
    name, sketch, origin = Owner(app, Member(item, "GetSketch"), owners)
    inverse = None if origin else Member(sketch.ModelToSketchTransform, "Inverse")
    try:
        local = (float(item.X), float(item.Y), float(item.Z))
    except AttributeError:
        kind = int(Member(item, "GetType"))
        construction = bool(item.ConstructionGeometry)
        fixed = any(int(Member(relation, "GetRelationType")) == 17 and not relation.Suppressed for relation in Bounded(Member(item, "GetRelations"), "segment relations", 1024))
        if kind == 0:
            start, end = Member(item, "GetStartPoint2"), Member(item, "GetEndPoint2")
            return {"kind": "line", "owner": name, "geometry": {"start_mm": World(inverse, (start.X, start.Y, start.Z)), "end_mm": World(inverse, (end.X, end.Y, end.Z))}, "construction": construction, "fixed": fixed}
        if kind == 1:
            center = Member(item, "GetCenterPoint2")
            geometry = {"center_mm": World(inverse, (center.X, center.Y, center.Z)), "radius_mm": float(Member(item, "GetRadius")) * 1000}
            if Member(item, "IsCircle"):
                return {"kind": "circle", "owner": name, "geometry": geometry, "construction": construction, "fixed": fixed}
            raise ValueError("native partial arc requires sweep and orientation measurement")
        raise ValueError(f"native sketch segment type {kind} requires a geometry collector")
    fixed = origin or any(int(Member(relation, "GetRelationType")) == 17 and not relation.Suppressed for relation in Bounded(Member(item, "GetRelations"), "point relations", 1024))
    if origin and (int(item.Type) not in (1, 8) or any(abs(value) > 1e-12 for value in local)):
        raise ValueError("document origin reference is not the native zero origin point")
    return {"kind": "point", "owner": name, "geometry": {"point_mm": [value * 1000 for value in local] if origin else World(inverse, local)}, "construction": origin, "fixed": origin or fixed}


def Dimensions(feature):
    display = Member(feature, "GetFirstDisplayDimension")
    result = []
    count = 0
    while display is not None:
        count += 1
        if count > 256:
            raise ValueError("native feature dimensions exceed 256 entries")
        dimension = display.GetDimension2(0)
        if str(dimension.FullName).split("@")[1:2] == [str(feature.Name)]:
            result.append((display, dimension))
        display = feature.GetNextDisplayDimension(display)
    return result


def DimensionName(dimension):
    return "@".join(str(dimension.FullName).split("@")[:2])


def Support(sketch):
    import pythoncom
    from win32com.client import VARIANT

    kind = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    support = sketch.GetReferenceEntity(kind)
    if support is None:
        raise ValueError("native sketch has no support reference")
    if int(kind.value) == 2:
        feature = Member(support, "GetFeature")
        if feature is None:
            raise ValueError("native sketch support face has no owning feature")
        return {"kind": "face", "feature": str(feature.Name)}
    if str(Member(support, "GetTypeName2")) != "RefPlane":
        raise ValueError("native sketch support requires a reference collector")
    if Member(support, "GetParents"):
        raise ValueError("constructed native support plane requires a definition collector")
    frame = Frame(Member(support, "GetSpecificFeature2").Transform)
    normal = Normal(frame)
    if any(abs(value) > 1e-6 for value in frame["origin_mm"]) or sum(abs(value) > 1e-9 for value in normal) != 1:
        raise ValueError("native support plane is not a principal plane")
    return {"kind": "principal_plane", "normal": normal}


def Sketch(app, feature, owners, gaps):
    name = str(feature.Name)
    sketch = owners[name]["sketch"]
    result = {"name": name, "frame": Frame(Member(sketch.ModelToSketchTransform, "Inverse")), "support": Support(sketch), "entities": [], "constraints": []}
    for entity in Bounded(Member(sketch, "GetSketchSegments"), name + " segments") + Bounded(Member(sketch, "GetSketchPoints2"), name + " points"):
        try:
            result["entities"].append(Entity(app, entity, owners))
        except Exception as error:
            gaps.append(f"sketch:{name}:entity:{type(error).__name__}:{str(error)[:160]}")
    bound_dimensions = set()
    for relation in Bounded(sketch.RelationManager.GetRelations(0), name + " relations"):
        try:
            code = int(Member(relation, "GetRelationType"))
            kind = {4: "horizontal", 5: "vertical", 6: "tangent", 7: "parallel", 8: "perpendicular", 9: "coincident", 10: "concentric", 11: "symmetric", 12: "midpoint", 14: "equal", 17: "fixed", 25: "horizontal", 26: "vertical", 27: "collinear"}.get(code)
            parameter, driving = None, True
            if code in (1, 2, 3, 15):
                display = Member(relation, "GetDisplayDimension")
                if display is None:
                    raise ValueError("native dimensional relation has no display dimension")
                dimension = display.GetDimension2(0)
                parameter = DimensionName(dimension)
                bound_dimensions.add(parameter)
                kind = {2: "distance", 11: "distance_x", 12: "distance_y", 3: "angle", 5: "radius", 6: "diameter"}.get(int(display.Type2))
                driving = int(dimension.DrivenState) == 2
                annotation = Member(display, "GetAnnotation")
                if annotation is None or Member(annotation, "IsDangling"):
                    raise ValueError("native dimension attachment is missing or dangling")
            if kind is None:
                raise ValueError(f"native relation type {code} requires a semantic collector")
            operands = Bounded(Member(relation, "GetDefinitionEntities2"), name + " relation operands", 64)
            if not operands:
                raise ValueError("native relation has no definition operands")
            result["constraints"].append({"kind": kind, "operands": [Entity(app, value, owners) for value in operands], "parameter": parameter, "driving": driving, "suppressed": bool(relation.Suppressed)})
        except Exception as error:
            gaps.append(f"sketch:{name}:constraint:{type(error).__name__}:{str(error)[:160]}")
    if bound_dimensions != {DimensionName(dimension) for _, dimension in Dimensions(feature)}:
        gaps.append(f"sketch:{name}:dimensions:relation_bindings_incomplete")
    return result


def Extrude(document, feature, owners, sketch_rows):
    import pythoncom
    from win32com.client import VARIANT

    creates_body = bool(Member(feature, "IsBase2"))
    definition = Member(feature, "GetDefinition")
    component = VARIANT(pythoncom.VT_DISPATCH, None)
    if definition is None or not definition.AccessSelections(document, component):
        raise ValueError("native extrusion selections are unavailable")
    try:
        parents = Bounded(Member(feature, "GetParents"), "extrusion parents", 4096)
        profiles = [parent for parent in parents if str(parent.Name) in owners and str(Member(parent, "GetTypeName2")) == "ProfileFeature"]
        if len(profiles) != 1:
            raise ValueError("native extrusion does not have exactly one planar sketch profile")
        profile = str(profiles[0].Name)
        if profile not in sketch_rows:
            raise ValueError("native extrusion profile semantics are incomplete")
        if definition.BothDirections or Member(definition, "IsThinFeature") or Member(definition, "GetContoursCount"):
            raise ValueError("two sided, thin or selected contour native extrusion requires a semantic collector")
        ref1 = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_DISPATCH, None)
        ref2 = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_DISPATCH, None)
        type1 = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
        type2 = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
        reference_count = int(definition.GetDirectionReference(ref1, type1, ref2, type2))
        if reference_count not in (-1, 0) or ref1.value is not None or ref2.value is not None or type1.value not in (-1, 0) or type2.value not in (-1, 0):
            raise ValueError("native extrusion has an authored direction reference")
        end = {0: "blind", 1: "through_all"}.get(int(definition.GetEndCondition(True)))
        if end is None:
            raise ValueError("native extrusion termination requires a reference collector")
        start = int(definition.FromType)
        if start not in (0, 3):
            raise ValueError("native extrusion start requires an entity reference collector")
        offset = float(definition.FromOffsetDistance) * 1000 * (-1 if definition.FromOffsetReverse else 1) if start == 3 else 0.0
        taper = float(definition.GetDraftAngle(True)) * (-1 if definition.GetDraftOutward(True) else 1) if definition.GetDraftWhileExtruding(True) else 0.0
        if taper or offset:
            raise ValueError("native extrusion taper or start offset requires unambiguous parameter role binding")
        boss = creates_body or bool(Member(definition, "IsBossFeature"))
        if not boss and (definition.FlipSideToCut or definition.NormalCut or definition.FeatureScope):
            raise ValueError("native cut side, sheet metal or explicit body scope requires a semantic collector")
        length = float(definition.GetDepth(True)) * 1000 if end == "blind" else None
        dimensions = Dimensions(feature)
        if length is not None:
            matches = [dimension for display, dimension in dimensions if int(display.Type2) in (2, 11, 12) and math.isclose(float(dimension.SystemValue) * 1000, length, abs_tol=1e-6, rel_tol=1e-9)]
            if len(dimensions) != 1 or len(matches) != 1:
                raise ValueError("native extrusion length parameter binding is ambiguous")
            binding = DimensionName(matches[0])
        else:
            if dimensions:
                raise ValueError("depthless native extrusion has unexpected owned dimensions")
            binding = None
        direction = Normal(sketch_rows[profile]["frame"])
        scale = -1 if (not boss) != bool(definition.ReverseDirection) else 1
        operation = "join" if boss and not creates_body and definition.Merge else "create" if boss else "cut"
        return {"name": str(feature.Name), "kind": "extrude", "dependencies": [str(parent.Name) for parent in parents if str(Member(parent, "GetTypeName2")) in ("ProfileFeature", "Extrusion", "ICE", "Boss", "Cut")], "operation": operation, "profile": profile, "length_mm": length, "end_condition": end, "direction": [scale * value for value in direction], "taper_rad": taper, "start_offset_mm": offset, "side_mode": "one_sided", "bindings": {"length": binding, "taper": None, "start_offset": None}}
    finally:
        Member(definition, "ReleaseSelectionAccess")


def MeasureSemantics(app, document, features):
    gaps = []
    result = {"schema": 1, "features": [], "sketches": [], "parameters": [], "gaps": gaps}
    owners = {str(feature.Name): {"sketch": Member(feature, "GetSpecificFeature2"), "origin": str(Member(feature, "GetTypeName2")) == "OriginProfileFeature"} for feature in features if str(Member(feature, "GetTypeName2")) in ("ProfileFeature", "OriginProfileFeature")}
    sketch_rows = {}
    for feature in features:
        if str(Member(feature, "GetTypeName2")) != "ProfileFeature":
            continue
        name = str(feature.Name)
        try:
            sketch_rows[name] = Sketch(app, feature, owners, gaps)
            result["sketches"].append(sketch_rows[name])
        except Exception as error:
            gaps.append(f"sketch:{name}:{type(error).__name__}:{str(error)[:160]}")
    equations = {}
    try:
        manager = Member(document, "GetEquationMgr")
        count = int(Member(manager, "GetCount"))
        if count > 4096:
            raise ValueError("native equations exceed 4096 entries")
        for index in range(count):
            text = str(manager.Equation(index))
            if "=" not in text:
                raise ValueError("native equation has no assignment")
            lhs, rhs = text.split("=", 1)
            name = lhs.strip().strip('"')
            if name in equations:
                raise ValueError("native equations have a duplicate assignment")
            equations[name] = rhs.strip()
    except Exception as error:
        gaps.append(f"equations:{type(error).__name__}:{str(error)[:160]}")
    excluded = {"CommentsFolder", "FavoriteFolder", "HistoryFolder", "SelectionSetFolder", "SensorFolder", "DocsFolder", "NotesAreaFtrFolder", "SurfaceBodyFolder", "SolidBodyFolder", "EnvFolder", "AmbientLight", "DirectionLight", "InkMarkupFolder", "EqnFolder", "MaterialFolder", "OriginProfileFeature", "DetailCabinet", "AnnotationView", "NotesArea", "FtrFolder", "Attribute", "ICEFolder"}
    for feature in features:
        name, kind = str(feature.Name), str(Member(feature, "GetTypeName2"))
        try:
            for display, dimension in Dimensions(feature):
                parameter = DimensionName(dimension)
                owner = Member(dimension, "GetFeatureOwner")
                if owner is None or int(app.IsSame(owner, feature)) != 1:
                    raise ValueError("native parameter owner differs from its feature")
                expression = equations.pop(parameter, None)
                state = int(dimension.DrivenState)
                if state not in (1, 2):
                    raise ValueError("native parameter driving state is unknown")
                result["parameters"].append({"name": parameter, "owner": name, "expression": expression, "dependencies": re.findall(r'"([^\"]+)"', expression) if expression else [], "role": "derived" if expression is not None else "driving" if state == 2 else "reference"})
            if kind in excluded:
                continue
            if kind == "RefPlane":
                if Member(feature, "GetParents"):
                    raise ValueError("constructed native plane requires a semantic collector")
                continue
            if kind == "ProfileFeature":
                result["features"].append({"name": name, "kind": "sketch", "dependencies": [str(parent.Name) for parent in Bounded(Member(feature, "GetParents"), "sketch parents", 4096) if str(Member(parent, "GetTypeName2")) in ("ProfileFeature", "Extrusion", "ICE", "Boss", "Cut")]})
            elif kind in ("Extrusion", "ICE", "Boss", "Cut"):
                result["features"].append(Extrude(document, feature, owners, sketch_rows))
            else:
                raise ValueError(f"native feature type {kind} requires a semantic collector")
        except Exception as error:
            gaps.append(f"feature:{name}:{type(error).__name__}:{str(error)[:160]}")
    if equations:
        gaps.append("equations:unbound_assignments:" + ",".join(sorted(equations))[:160])
    return result
