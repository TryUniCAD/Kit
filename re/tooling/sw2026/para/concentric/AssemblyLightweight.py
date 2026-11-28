from functools import partial
from itertools import product
from math import isfinite
from struct import pack, unpack

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.ExternalFields import KExternalFields
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.PartMatFields import KPartMatFields
from convert.adapters.solidworks.Archive.Bodies.Layouts.ContainerFields import KContainerFields
from convert.adapters.solidworks.Archive.Bodies.Layouts.GeometryFields import KGeometryFields
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.GeometryFields import KGeometryFields as ResolvedGeometry
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField as Field
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.MakeBox import MakeBox
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeRawIdentity import MakeRawIdentity
from convert.adapters.solidworks.Archive.Construction.System.MakeDefaultData import MakeDefaultData
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import PrincipalFrame
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadNodeName, RequireNode


HELPER = RuntimeClass("moLWdataHelper_c", 1)
HATCH = RuntimeClass("gcXhatch_c", 1)
LIGHT_PLANE = RuntimeClass("moLWPlaneNodeData_c", 1)
PLANE = RuntimeClass("moRefPlane_c", 1)
DATA = RuntimeClass("moDefaultRefPlnData_c", 1)
FEATURE_BASE = "moLWFeatureNodeData_c"
TRANSFORM = "mgXform_c.operator>>"
MEMBER = "Contents/Config-0-LWDATA"
ENGLISH_HATCH = "ANSI31 (Iron BrickStone)"
BOX_KEYS = tuple(f"b{i}" for i in range(10))
BORDER_KEYS = BOX_KEYS[:4]
LIST_KEYS = ("f78", "fc0", "f158", "f110")
EMPTY_COUNTS = ("f108", "f10c", "point_count", "coordinate_system_count")
OTHER_DATUM_CLASSES = frozenset(
    {"moRefAxis_c", "moConnectionPoint_c", "moRoutePoint_c", "moRefPoint_c", "moCoordSys_c"}
)
LAYOUTS = KExternalFields | KPartMatFields | KContainerFields | KGeometryFields | ResolvedGeometry | {
    FEATURE_BASE: (
        Field("Text", "f08"),
        Field("Text", "f10"),
        Field("Scalar", "f18", "i32"),
        Field("Scalar", "f1c", "i32"),
        Field("Scalar", "f20", "i32"),
    ),
    LIGHT_PLANE.NameValue: (
        Field("Base", FEATURE_BASE),
        Field("Embed", "f30", "mgPoint_c.restore"),
        Field("Embed", "f48", "mgVector_c.restore"),
        Field("Embed", "f60", "mgBBox_c.restore"),
        Field("Embed", "fb8", TRANSFORM),
        Field("Scalar", "f140", "i32"),
        *(Field("Scalar", key, "f64") for key in BORDER_KEYS),
        Field("Text", "f168"),
    ),
    HELPER.NameValue: (
        Field("Scalar", "f70", "i32"),
        Field("Embed", "f08", "mgBBox_c.restore"),
        Field("Scalar", "f68", "f64"),
        Field("Node", "f60", HATCH.NameValue),
        *(Field("Embed", key, "suObList") for key in LIST_KEYS),
        *(Field("Scalar", key, "i32") for key in EMPTY_COUNTS),
    ),
}
SCHEMAS = {cls.NameValue: (cls.SchemaValue,) for cls in (HELPER, HATCH, LIGHT_PLANE)}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def context():
    return BodyContext(19000, LAYOUTS, {}, SCHEMAS)


def encode(graph):
    writer = BodyWriter(ArchiveMaps(1), context(), WriteBodyMut)
    WriteBodyMut(writer, graph)
    return bytes(writer.OutputValue)


def decode(payload):
    current = context()
    cursor = BinaryReader(payload)
    reader = GraphReader(cursor, ArchiveMaps(1), partial(ReadBodyMut, current), RequireCanonicalTags=True)
    graph = ArchiveNode(HELPER, {})
    ReadBodyMut(current, reader, graph)
    fields = graph.FieldsValue
    planes = tuple(row["o"] for row in fields["f78"]["items"])
    require(not cursor.GetRemaining() and encode(graph) == payload
            and all(not fields[key]["items"] for key in LIST_KEYS[1:])
            and all(fields[key] == 0 for key in EMPTY_COUNTS)
            and fields["f68"] == 0.0 and fields["f60"].ClassValue == HATCH
            and len(planes) == len(set(planes)) == 3
            and all(plane.ClassValue == LIGHT_PLANE for plane in planes),
            "lightweight archive requires the exact three-plane empty-auxiliary branch")
    return graph, planes


def stamp(headers):
    first, second = (RequireNode(header, "moHeader_c") for header in headers)
    value = FieldInt(first.FieldsValue, "f40")
    require(first is not second and value == FieldInt(second.FieldsValue, "f40")
            and 0 <= value < 2**31, "lightweight update stamp differs between the actual headers")
    return value


def bounds(root):
    fields = RequireNode(root, "moAssembly_c").FieldsValue
    first, second = (fields.get(key) for key in ("f1a18", "f1a20"))
    require(first is not None and first == second and tuple(first) == BOX_KEYS
            and all(type(value) is float and isfinite(value) for value in first.values()),
            "lightweight sizing requires the matched resolved assembly bounds")
    low = tuple(first[key] for key in BOX_KEYS[6:9])
    high = tuple(first[key] for key in BOX_KEYS[3:6])
    require(all(b - a > 1e-7 for a, b in zip(low, high, strict=True)) and first["b9"] > 0,
            "lightweight sizing requires a finite nondegenerate assembly envelope")
    return first, low, high


def select_planes(roots):
    authored = tuple(node for node in roots if node is not None)
    require(not any(node.ClassValue.NameValue in OTHER_DATUM_CLASSES for node in authored),
            "lightweight archive lacks the additional native datum cache owner")
    planes = tuple(node for node in authored if node.ClassValue == PLANE)
    require(len(planes) == len({FieldInt(p.FieldsValue, "f08") for p in planes}) == 3,
            "lightweight archive requires three distinct actual principal planes")
    return planes


def vector(values):
    return tuple(values[k] for k in "xyz")


def point(values):
    return dict(zip("xyz", values, strict=True))


def plane_owner(plane):
    p = RequireNode(plane, PLANE.NameValue).FieldsValue
    data = RequireNode(p["f6f8"], DATA.NameValue)
    f = data.FieldsValue
    normal = vector(f["normal"])
    candidates = tuple(axis for axis in "xyz" if PrincipalFrame(axis).NormalValue == normal)
    require(len(candidates) == 1 and p["f2b0"] == 19000 and p["f298"] == 0 and p["f2a8"] & 1 == 0
            and p["f6dc"] & 3 == 1 and FieldInt(p, "f08") > 0,
            "lightweight archive requires an unsuppressed hidden canonical datum")
    axis, = candidates
    frame = PrincipalFrame(axis)
    original = MakeDefaultData(axis, frame).FieldsValue
    require(all(f[k] == original[k] for k in ("root", "normal", "f20", "f54")),
            "lightweight archive requires the actual unchanged principal carrier")
    return (p, f, axis, frame)


def project_display(low, high, axis, frame):
    spans = (b - a for a, b in zip(low, high, strict=True))
    by_axis = tuple(span * 0.5 + span * 0.05 for span in spans)
    center = tuple(0.0 if coordinate == axis else (a + b) * 0.5
                   for coordinate, a, b in zip("xyz", low, high, strict=True))
    w, h = (by_axis[next(i for i, value in enumerate(tangent) if value != 0.0)]
            for tangent in (frame.AxisU, frame.AxisV))
    borders = dict(zip(BORDER_KEYS, (w, -w, h, -h), strict=True))
    corners = tuple(tuple(o + (u * x + v * y) for o, x, y in zip(center, frame.AxisU, frame.AxisV, strict=True))
                    for u, v in product((-w, w), (h, -h)))
    coordinates = tuple(zip(*corners, strict=True))
    box = MakeBox(tuple(min(values) for values in coordinates), tuple(max(values) for values in coordinates))
    return {"display_root": point(center), **borders}, point(corners[0]), box


def raw_frame(canonical):
    if canonical["has_matrix"] == 0:
        return MakeRawIdentity()
    rotation = tuple(canonical["f08"][f"m{i}"] for i in range(9))
    translation_and_scale = tuple(canonical[key] for key in ("f58", "f60", "f68", "f70"))
    payload = pack("<9dII4dII", *rotation, 0, 0, *translation_and_scale, canonical["f78"], 0)
    return {"words": tuple({"w": word} for word in unpack("<30I", payload))}


def ordinary_hatch(locale, name):
    require((locale, name) == ("en-US", ENGLISH_HATCH),
            "lightweight archive lacks the selected localized assembly hatch")
    return ArchiveNode(HATCH, {
        "f08": CStringValue(name, True),
        "f10": 0.0,
        "f18": 1.0,
        "f34": 0,
        "f20": 0,
        "f24": 1,
        "f28": -1,
        "f2c": -1,
        "f30": 0,
    })


def build(root, headers, roots, *, locale, hatch_name, fresh=False):
    assembly_bounds, low, high = bounds(root)
    current_stamp = stamp(headers)
    hatch = ordinary_hatch(locale, hatch_name)
    selections = select_planes(roots)
    if fresh:
        require(headers[0].FieldsValue["f38"] is headers[1].FieldsValue["f38"]
                and all(plane.FieldsValue.get("owner") is root for plane in selections),
                "lightweight construction requires the actual generated root and its paired self file")
    plans, made, axes = [], [], []
    for node in selections:
        fields, data, axis, frame = plane_owner(node)
        display, name_corner, box = project_display(low, high, axis, frame)
        if fresh:
            require(data == MakeDefaultData(axis, frame).FieldsValue and fields["f6c0"] == point(frame.OriginValue),
                    "lightweight construction requires an unset generated datum display")
            plans.append((fields, data, display, name_corner))
        else:
            require(all(data[key] == value for key, value in display.items()) and fields["f6c0"] == name_corner,
                    "lightweight geometry differs from its actual linked datum display owners")
        axes.append(axis)
        made.append({"o": ArchiveNode(LIGHT_PLANE, {
            "f08": CStringValue(node.ClassValue.NameValue, True),
            "f10": CStringValue(ReadNodeName(node), True),
            "f18": FieldInt(fields, "f08"),
            "f1c": int(fields["f298"] == 1),
            "f20": int(fields["f6dc"] & 3 == 1),
            "f30": dict(data["root"]),
            "f48": dict(data["normal"]),
            "f60": box,
            "fb8": raw_frame(data["f20"]),
            "f140": FieldInt(data, "f54"),
            **{key: display[key] for key in BORDER_KEYS},
            "f168": CStringValue(DATA.NameValue, True),
        })})
    require(set(axes) == set("xyz"), "lightweight archive requires all three principal axes")
    graph = ArchiveNode(HELPER, {
        "f70": current_stamp,
        "f08": dict(assembly_bounds),
        "f68": 0.0,
        "f60": hatch,
        "f78": {"items": tuple(made)},
        **{key: {"items": ()} for key in LIST_KEYS[1:]},
        **dict.fromkeys(EMPTY_COUNTS, 0),
    })
    payload = encode(graph)
    for fields, data, display, name_corner in plans:
        data.update(display)
        fields["f6c0"] = name_corner
    return payload
