from math import isclose, isfinite

from convert.adapters.solidworks.Archive.Construction.Datums.MakeHingePick import MakeHingePick
from convert.adapters.solidworks.Archive.Construction.Datums.PutHingeViews import PlanHingeView
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import RequireRootNode
from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import KAtomLists, KAtomWords
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import InitFeatureMut
from convert.adapters.solidworks.Archive.Construction.Origin.MakeOriginRef import MakeOriginRef
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Construction.PlanarMates.SignedStamp import SignedStamp
from convert.adapters.solidworks.Archive.Construction.PlanarMates.WrapperFields import WrapperFields
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import PrincipalFrame
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadNodeName, RequireNode, RequireRecord


def dot(first, other):
    return sum(a * b for a, b in zip(first, other, strict=True))


def cross(first, other):
    ax, ay, az = first
    bx, by, bz = other
    return (ay*bz - az*by, az*bx - ax*bz, ax*by - ay*bx)


def point(coordinates):
    return dict(zip("xyz", coordinates, strict=True))


def coords(row):
    return tuple(row[key] for key in "xyz")


def put_principal_displays(system, bounds):
    lower, upper = bounds
    if len(lower) != len(upper) or len(lower) != 3 or not all(map(isfinite, (*lower, *upper))):
        raise ValueError("datum sizing needs finite world bounds")
    sizes = tuple(high - low for low, high in zip(lower, upper, strict=True))
    if min(sizes) <= 1e-7 or not all(low <= 0 <= high for low, high in zip(lower, upper, strict=True)):
        raise ValueError("datum sizing needs a nondegenerate stock meeting the model origin")
    RequireRootNode(system.RootValue, "moPart_c")
    if set(system.SystemValues.PlaneValues) != {"x", "y", "z"}:
        raise ValueError("datum sizing needs exactly the actual principal supports")
    center = tuple((low + high) * 0.5 for low, high in zip(lower, upper, strict=True))
    plans = []
    for axis in "xyz":
        frame = PrincipalFrame(axis)
        station = dot(center, frame.NormalValue)
        display_root = tuple(a - station * b for a, b in zip(center, frame.NormalValue, strict=True))
        width, height = (dot(sizes, tuple(map(abs, basis))) for basis in (frame.AxisU, frame.AxisV))
        margin_u = width * 0.5 + width * 0.05
        margin_v = height * 0.5 + height * 0.05
        plans.append(PlanHingeView(system, axis, display_root, (margin_u, -margin_u, margin_v, -margin_v)))
    for plane, geometry, display, corner in plans:
        geometry.FieldsValue.update(display)
        plane.FieldsValue["f6c0"] = corner


def first_plane_interval(plane, axis, direction):
    data = RequireNode(plane.FieldsValue["f6f8"], "moDefaultRefPlnData_c").FieldsValue
    frame = PrincipalFrame(axis)
    picks = [(dot(basis, direction), keys) for basis, keys in ((frame.AxisU, ("b0", "b1")),
                                                              (frame.AxisV, ("b2", "b3")))
             if dot(basis, direction)]
    if len(picks) != 1 or abs(picks[0][0]) != 1 or dot(frame.NormalValue, direction) != 0:
        raise ValueError("named axis must lie on a real principal display direction")
    sign, borders = picks[0]
    center = dot(coords(RequireRecord(data["display_root"])), direction)
    low, high = sorted(center + sign * data[key] for key in borders)
    if not low < 0 < high:
        raise ValueError("the selected finite plane must straddle the axis root")
    return (low, high)


def pick_plane(system, axis, headers):
    plane = system.SystemValues.PlaneValues[axis]
    if axis != "z":
        return MakeHingePick(system, plane, axis, headers)
    owner_id = FieldInt(plane.FieldsValue, "f08")
    created = DatumTime(headers[0], owner_id)
    if DatumTime(headers[1], owner_id) != created:
        raise ValueError("Front support creation differs between its own headers")
    data = RequireNode(plane.FieldsValue["f6f8"], "moDefaultRefPlnData_c").FieldsValue
    transform = RequireRecord(data["f20"])
    if transform["has_matrix"] != 0 or "f08" in transform:
        raise ValueError("ordinary Front support requires the typed identity-matrix branch")
    reference = MakeOriginRef(plane, system.RootValue, axis)
    reference.FieldsValue["ff0"] = {**RequireRecord(reference.FieldsValue["ff0"]), "f08": created}
    fields = WrapperFields(reference)
    fields.update(f68=1, f08=SignedStamp(FieldInt(headers[0].FieldsValue, "f40")),
                  f0c=FieldInt(system.ConfigValues[0].FieldsValue, "f08"),
                  fd0=dict(RequireRecord(data["root"])), fe8=dict(RequireRecord(data["normal"])),
                  f100=dict(transform), f188=point((0.0, 0.0, 0.0)))
    fields.update({key: data[f"b{index}"] for index, key in enumerate(("fb0", "fb8", "fc0", "fc8"))})
    return ArchiveNode(RuntimeClass("moPlaneRef_w", 1), fields)


def validate_axis_intents(axes, current_names):
    if not isinstance(axes, list) or len(axes) != 3:
        raise ValueError("origin axes need the three ordered authored principal roles")
    names = set(current_names)
    outputs = []
    for data, axis, expected in zip(axes, "xyz", ((1., 0., 0.), (0., 1., 0.), (0., 0., 1.)), strict=True):
        if type(data) is not dict or set(data) != {"role", "name", "origin", "direction", "visible"}:
            raise ValueError("unsupported authored axis record")
        name = data["name"]
        direction = data["direction"]
        if (type(name) is not str or not name or not name.isprintable() or name in names
                or data["visible"] is not True or data["role"] != axis.upper() + "_Axis"
                or data["origin"] != [0., 0., 0.] or type(direction) is not list or len(direction) != 3
                or not all(type(a) in (float, int) and isclose(a, b, rel_tol=0, abs_tol=1e-14)
                           for a, b in zip(direction, expected, strict=True))):
            raise ValueError("unsupported axis name, carrier, order or model visibility")
        names.add(name)
        outputs.append((name, expected))
    return outputs


def make_axis_nodes(system, settings, allocator, headers, bounds, axes, stock_roots):
    intents = validate_axis_intents(axes, map(ReadNodeName, stock_roots))
    if (len(system.ConfigValues) != 1 or system.ManagerValue.FieldsValue["f360"] is not system.ConfigValues[0]):
        raise ValueError("origin axes require a single actual active part configuration")
    put_principal_displays(system, bounds)
    outputs = []
    for (name, intended), (first, second) in zip(intents, (("y", "z"), ("z", "x"), ("x", "y")), strict=True):
        direction = cross(PrincipalFrame(first).NormalValue, PrincipalFrame(second).NormalValue)
        if direction != intended:
            raise ValueError("selected principal supports do not produce the authored signed direction")
        stations = first_plane_interval(system.SystemValues.PlaneValues[first], first, direction)
        start, end = (point(tuple(station * component if component else 0.0 for component in direction))
                      for station in stations)
        feature = ArchiveNode(RuntimeClass("moRefAxis_c", 1), {})
        InitFeatureMut(feature, name, system.RootValue, settings.TargetValue, allocator)
        feature.FieldsValue.update(dict.fromkeys(KAtomWords, 0))
        feature.FieldsValue.update({key: [] for key in KAtomLists})
        feature.FieldsValue.update(f35c=0, f368={"n": 0, "items": []}, f388={"n": 0, "items": []},
                                   f538=None, f4a0=1, f6c0=start, f6dc=4, f6e0=0, f6e8=None, f6f0=0)
        feature.FieldsValue["f700"] = ArchiveNode(RuntimeClass("moPlaneInterAxisData_c", 1), {
            "f18": start, "f30": end, "f08": -stations[0], "f10": stations[1], "f50": point(direction),
            "f68": point((0.0, 0.0, 0.0)), "f80": pick_plane(system, first, headers),
            "f88": pick_plane(system, second, headers),
        })
        outputs.append(feature)
    return tuple(outputs)
