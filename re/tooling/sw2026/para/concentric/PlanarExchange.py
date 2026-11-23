from math import fsum, isclose

from AssemblyModelExchange import ordinary_feature
from ExchangeMateEndpoints import project_exchange_target
from ExchangePack import OrderedMap

from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt, ReadNodeName, ReadRows, RequireNode, RequireRecord,
)
from convert.adapters.solidworks.Assembly.PlanarMates.ReadDistance import ReadDistance
from convert.adapters.solidworks.Assembly.PlanarMates.ReadPlane import ReadPlane, ReadVector
from convert.adapters.solidworks.Core.TypedMates.CheckMateIds import CheckMateIds
from convert.adapters.solidworks.Core.TypedMates.CheckMateMode import CheckMateMode
from convert.adapters.solidworks.Core.TypedMates.CheckMateWrappers import CheckMateWraps
from convert.adapters.solidworks.Core.TypedMates.Cold.ReadMateDim import ReadMateDim


COINCIDENT = "moMateCoincident"
DISTANCE = "moMateDistanceDim_c"


def project_planar_exchange_ref(root, active, identity, index):
    wrapper = RequireNode(active, "moPlaneRef_w")
    component = ReadPlane(wrapper, identity, index, FieldInt(root.FieldsValue, "fd48"))
    fields = component.FieldsValue
    plane = RequireRecord(fields.get("ff0"))
    feature = FieldInt(plane, "f00")
    if (
        set(plane) != {"f00", "f08"}
        or not 0 < feature <= 0x7FFFFFFF
        or FieldInt(fields, "f4c") != 19000
        or FieldInt(fields, "f100") not in (1, 2, 3)
        or FieldInt(wrapper.FieldsValue, "f70") != 19000
    ):
        raise ValueError("planar exchange requires the live selected principal feature identity")
    occurrence, target = project_exchange_target(root, component)
    position = RequireRecord(occurrence.FieldsValue.get("f3c0"))
    if (
        FieldInt(position, "f10") != FieldInt(wrapper.FieldsValue, "f0c")
        or (FieldInt(wrapper.FieldsValue, "f08") & 0xFFFFFFFF)
        != FieldInt(occurrence.FieldsValue, "f3e0")
        or FieldInt(occurrence.FieldsValue, "f2c") != 0
    ):
        raise ValueError("planar exchange wrapper configuration or occurrence update differs")
    return occurrence, OrderedMap(
        (
            ("class", "moPlaneRef_w"),
            ("dummy", OrderedMap(
                (("class", "moCompRefPlane_c"), ("featureID", str(feature)), ("target", target))
            )),
        )
    )


def project_distance_entries(mate):
    dimension = ReadMateDim(mate)
    parameter = RequireNode(dimension.FieldsValue.get("f28"), "moLengthParameter_c")
    if ReadNodeName(parameter) != "D1":
        raise ValueError("planar exchange requires the ordinary live D1 length")
    return (
        ("Distance", ReadDistance(mate)),
        ("FlipDim", int(FieldInt(mate.FieldsValue, "f4c0") == 0)),
    )


def check_aligned_planes(active, distance):
    first, second = (RequireNode(row.get("o"), "moPlaneRef_w").FieldsValue for row in active)
    axis, other_axis = (ReadVector(fields.get("fe8")) for fields in (first, second))
    products = (fsum(x * y for x, y in zip(a, b, strict=True))
                for a, b in ((axis, axis), (other_axis, other_axis), (axis, other_axis)))
    if any(not isclose(value, 1.0, rel_tol=0.0, abs_tol=1e-10) for value in products):
        raise ValueError("planar exchange requires aligned unit world planes")
    start, end = (ReadVector(fields.get("fd0")) for fields in (first, second))
    gap = fsum((b - a) * n for a, b, n in zip(start, end, axis, strict=True))
    if distance is None:
        if not isclose(gap, 0.0, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError("planar exchange coincident planes must share their world offset")
    elif gap <= 0.0 or not isclose(gap, distance, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("planar exchange requires positive signed separation at the live distance")


def project_planar_exchange_cell(root, mate):
    native_class = mate.ClassValue.NameValue
    if native_class not in (COINCIDENT, DISTANCE):
        raise ValueError("planar exchange covers ordinary coincident and distance mate cells")
    name, identity, stamp = ordinary_feature(mate, native_class)
    fields = mate.FieldsValue
    CheckMateMode(mate)
    if (
        FieldInt(fields, "f35c") != 0
        or FieldInt(fields, "hidden") != 0
        or FieldInt(fields, "f2c") != 0
        or FieldInt(fields, "f2b0") != 19000
    ):
        raise ValueError("planar exchange requires an active visible current mate")
    active = ReadRows(fields.get("f410"))
    if len(active) != 2:
        raise ValueError("planar exchange requires two ordered live plane references")
    endpoints = tuple(
        project_planar_exchange_ref(root, row.get("o"), identity, index)
        for index, row in enumerate(active)
    )
    if endpoints[0][0] is endpoints[1][0]:
        raise ValueError("planar exchange requires distinct occurrence selections")
    extras = project_distance_entries(mate) if native_class == DISTANCE else ()
    check_aligned_planes(active, extras[0][1] if extras else None)
    return OrderedMap(
        (
            ("Aligment", FieldInt(fields, "f3b4")),
            *extras,
            ("NumberEntities", len(endpoints)),
            *((f"Ref{index}", value) for index, (_, value) in enumerate(endpoints)),
            ("class", native_class),
            ("description", name),
            ("hidden", False),
            ("id", identity),
            ("suppressed", False),
            ("updatestamp", stamp),
        )
    )


def project_planar_exchange(link, mates):
    root = RequireNode(link.ConfigValue.RootValue, "moAssembly_c")
    if not mates:
        return ()
    CheckMateIds(mates, link)
    CheckMateWraps(mates)
    return tuple(project_planar_exchange_cell(root, mate) for mate in mates)
