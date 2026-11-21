from convert.adapters.solidworks.Archive.Construction.System.MakeDefaultData import MakeDefaultData
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import PartSystem
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import PrincipalFrame
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireNode

from PatternHingeGeometry import ORIGIN, principal_displays


def point(values):
    return dict(zip("xyz", values, strict=True))


def name_corner(center, borders, frame):
    return tuple(origin + (borders[1] * u + borders[2] * v)
                 for origin, u, v in zip(center, frame.AxisU, frame.AxisV, strict=True))


def put_principal_displays_mut(system, bounds):
    if type(system) is not PartSystem or system.RootValue.ClassValue.NameValue != "moPart_c":
        raise ValueError("local datum sizing requires its real generated part system")
    if set(system.SystemValues.PlaneValues) != {"x", "y", "z"}:
        raise ValueError("local datum sizing requires all actual canonical owners")
    displays = principal_displays(bounds)
    plan = []
    roots = system.FeatureValues
    for axis, role in (("y", "Top Plane"), ("x", "Right Plane")):
        node = RequireNode(system.SystemValues.PlaneValues[axis], "moRefPlane_c")
        frame = PrincipalFrame(axis)
        native = RequireNode(node.FieldsValue.get("f6f8"), "moDefaultRefPlnData_c")
        if (sum(other is node for other in roots) != 1 or node.FieldsValue.get("owner") is not system.RootValue
                or native.FieldsValue != MakeDefaultData(axis, frame).FieldsValue
                or node.FieldsValue.get("f6c0") != point(ORIGIN)):
            raise ValueError("local datum sizing requires unchanged principal owners and absent presentation")
        display = displays[role]
        center, borders = display["display_root_m"], display["borders_m"]
        corner = name_corner(center, borders, frame)
        plan.append((node, native, {"display_root": point(center), **{f"b{i}": v for i, v in enumerate(borders)}}, corner))
        display["name_location_m"] = corner
    for node, native, fields, corner in plan:
        native.FieldsValue.update(fields)
        node.FieldsValue["f6c0"] = point(corner)
    return displays
