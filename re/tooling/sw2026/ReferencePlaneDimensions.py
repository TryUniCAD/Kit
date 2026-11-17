import operator

from AuthorCurves import require
from ReferencePlaneSourcePlan import BOSS, PLANE, SKETCH


def member(author, value, interface, name, *arguments):
    kind = 2 if name in ("Name", "FullName", "SystemValue", "DrivenState", "ReadOnly", "Type2") else 1
    declarations = [row for row in author.api["interfaces"][interface]["members"]
                    if row["names"][0] == name and row["invoke_kind"] == kind]
    require(len(declarations) == 1, "dimension ownership member is not uniquely bound in the pinned type library")
    declared, = declarations
    typed = author.declared_interface(value, interface)
    result = author.rec.call(interface + "." + name, typed._oleobj_.Invoke,
                            declared["member_id"], 0, declared["invoke_kind"], True, *arguments,
                            parameters={"interface": interface, "member_id": declared["member_id"],
                                        "invocation_kind": declared["invoke_kind"], "argument_count": len(arguments)})
    if result is not None and hasattr(result, "QueryInterface") and not hasattr(result, "_oleobj_"):
        return author.sw.wc.Dispatch(result)
    return result


def identity(author, first, second, label):
    observed = int(member(author, author.app, "ISldWorks", "IsSame", first, second))
    left = author.rec.call(label + " first canonical IUnknown", first._oleobj_.QueryInterface,
                           author.sw.pythoncom.IID_IUnknown)
    right = author.rec.call(label + " second canonical IUnknown", second._oleobj_.QueryInterface,
                            author.sw.pythoncom.IID_IUnknown)
    same_unknown = bool(author.rec.call(label + " canonical IUnknown equality", operator.eq, left, right))
    enums = author.api["enums"]["swObjectEquality"]
    require(observed in enums.values(), "native object equality returned an undeclared state")
    require(observed == enums["swObjectSame"] or
            observed == enums["swObjectUnsupported"] and same_unknown,
            label + " does not bind the same native object")
    return {"native_object_equality": observed, "canonical_iunknown_equal": same_unknown,
            "same_native_object": True}


def feature(author, name):
    value = author.get(author.model, "FeatureByName", name)
    require(value is not None, "named source feature is absent")
    require(str(member(author, value, "IFeature", "Name")) == name, "named source lookup returned a different feature")
    kind = str(member(author, value, "IFeature", "GetTypeName2"))
    expected = {PLANE: "RefPlane", SKETCH: "ProfileFeature", BOSS: "Boss"}[name]
    require(kind == expected, "named source feature has a different native kind")
    return value


def dimension(author, feature_name, mode, expected=None, creation_role=None):
    owner = feature(author, feature_name)
    parameter_name = "D1@" + feature_name
    parameter = author.get(author.model, "Parameter", parameter_name)
    require(parameter is not None, "named driving parameter is absent")
    full_name = str(member(author, parameter, "IDimension", "FullName"))
    require(full_name.split("@")[:2] == parameter_name.split("@"), "named parameter belongs to another feature")
    require(int(member(author, parameter, "IDimension", "DrivenState")) == 2 and
            not bool(member(author, parameter, "IDimension", "ReadOnly")), "named source parameter is not editable and driving")
    value = float(member(author, parameter, "IDimension", "SystemValue"))
    if expected is not None:
        author.rec.close_number("owned " + mode + " driving value", value, expected)
    comparison = None
    if creation_role in author.dimension_objects:
        comparison = identity(author, parameter, author.dimension_objects[creation_role], "creation/named driving parameter")
    traversal, matches = [], []
    display = member(author, owner, "IFeature", "GetFirstDisplayDimension")
    while display is not None:
        require(len(traversal) < 12, "feature display traversal exceeded its bounded small source scope")
        linked = member(author, display, "IDisplayDimension", "GetDimension2", 0)
        require(linked is not None, "native display has no linked dimension")
        name = str(member(author, linked, "IDimension", "FullName"))
        native_value = float(member(author, linked, "IDimension", "SystemValue"))
        kind = int(member(author, display, "IDisplayDimension", "Type2"))
        require(name not in {row["full_name"] for row in traversal}, "feature display traversal repeats a dimension")
        row = {"full_name": name, "value_m": native_value, "display_type": kind,
               "matches_requested_parameter": name.split("@")[:2] == parameter_name.split("@")}
        traversal.append(row)
        if row["matches_requested_parameter"]:
            type_name = "swRadialDimension" if mode == "radius" else "swLinearDimension"
            require(kind == author.api["enums"]["swDimensionType_e"][type_name], "owned display has the wrong physical dimension type")
            row["identity"] = identity(author, parameter, linked, "display/named driving parameter")
            author.rec.close_number("owned display driving value", native_value, value)
            matches.append(row)
        display = member(author, owner, "IFeature", "GetNextDisplayDimension", display)
    require(len(matches) == 1, "named driving parameter lacks exactly one owned display binding")
    owner_again = feature(author, feature_name)
    owner_identity = identity(author, owner, owner_again, "fresh source feature lookup")
    return parameter, {"name": parameter_name, "full_name": full_name, "value_m": value, "driving": True,
                       "editable": True, "unit_basis": "IDimension.SystemValue SI metres",
                       "owner_identity": owner_identity, "creation_identity": comparison,
                       "display_traversal": traversal, "matching_display_count": len(matches)}


def circle_geometry(author, sketch_feature, expected_radius):
    sketch = member(author, sketch_feature, "IFeature", "GetSpecificFeature2")
    require(sketch is not None, "named profile has no native sketch")
    segments = list(author.get(sketch, "GetSketchSegments") or ())
    require(len(segments) == 1, "source profile does not contain exactly one circle")
    arc = author.typed(segments[0], "SketchArc")
    require(bool(author.get(arc, "IsCircle")) and not bool(author.get(segments[0], "ConstructionGeometry")),
            "source radial parameter is not attached to an ordinary circle")
    actual = float(author.get(arc, "GetRadius"))
    author.rec.close_number("independent circle geometry radius", actual, expected_radius)
    center = author.point(author.get(arc, "GetCenterPoint2"))
    for coordinate in center:
        author.rec.close_number("independent circle local center", coordinate, 0.0)
    return {"radius_m": actual, "center_local_m": center, "ordinary_circle": True,
            "entity_binding": author.entity_binding(segments[0], "segment")}
