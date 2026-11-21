from dataclasses import dataclass
from math import fsum, isclose

from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakeSharedCopy import MakeSharedCopy
from convert.adapters.solidworks.Archive.Construction.Files.MakeFileConfig import MakeFileConfig
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireNode
from para.Tracking import signed_dword


@dataclass(frozen=True)
class CylinderFace:
    origin: tuple[float, float, float]
    axis: tuple[float, float, float]
    radius: float
    rim_centres: tuple[tuple[float, float, float], ...]
    feature_id: int
    creation: int
    marker: int
    caps: tuple[tuple[int, int], ...]
    node_id: int
    tag: int
    body_atom: int


def node(name, fields):
    return ArchiveNode(RuntimeClass(name, 1), fields)


def words(nodes, owner, name, field):
    attribute_index = owner.fields["attributes_features"]
    found = []
    visited = set()
    while attribute_index:
        if attribute_index in visited:
            raise ValueError("cycle in generated owner attribute chain")
        visited.add(attribute_index)
        attribute = nodes[attribute_index]
        definition = nodes[attribute.fields["definition"]]
        identifier = nodes[definition.fields["identifier"]]
        if identifier.fields["string"] == name:
            found.append(attribute.fields["fields"][field])
        attribute_index = attribute.fields["next"]
    value, = found
    return nodes[value].fields["values"]


def make_face(attachment):
    child = attachment.candidate
    projection = attachment.projection
    nodes = {item.index: item for item in projection.partition.nodes}
    side, = (item for item in nodes.values()
             if item.kind == 14 and item.fields["node_id"] == projection.lateral_face_node_id)
    body, = (item for item in nodes.values() if item.kind == 12)
    carrier = nodes[side.fields["surface"]]
    if carrier.kind != 51 or carrier.fields["owner"] != side.index:
        raise ValueError("lateral selection requires its actual cylinder")
    local = carrier.fields
    origin, axis, radius = local["pvec"], local["axis"], local["radius"]
    feature = child.BossValue.FeatureValue.FieldsValue["f08"]
    creation = DatumTime(child.HeaderValue, feature)
    marker = child.ProfileValue.GeometryValue.ArcValue.FieldsValue["f08"]
    epoch = signed_dword(creation)
    if words(nodes, side, "FACE_ID_2001", 2) != (74, feature, epoch, 0, marker):
        raise ValueError("cylinder lateral kernel identity has a different producing arc")
    atom, = words(nodes, body, "ATOM_ID_2001", 1)
    tag = projection.lateral_face_tag
    stamp, = words(nodes, side, "SWEntUnchanged", 0)
    if type(tag) is not int or (stamp >> 16) & 0xffff != tag & 0xffff or atom != attachment.atom_id:
        raise ValueError("cylinder face tag or body atom is foreign to its generated kernel owner")
    caps, centres, limits = [], [], []
    loop = side.fields["loop"]
    for _ in range(2):
        if not loop:
            raise ValueError("generated cylinder lacks a second lateral rim")
        member = nodes[loop]
        fin = nodes[member.fields["halfedge"]]
        other = nodes[fin.fields["other"]]
        cap = nodes[nodes[other.fields["loop"]].fields["face"]]
        plane = nodes[cap.fields["surface"]]
        curve = nodes[nodes[fin.fields["edge"]].fields["curve"]]
        kind, owner_id, birth, flags, selector, contour = words(nodes, cap, "FACE_ID_2001", 2)
        if plane.kind != 50 or (kind, owner_id, birth, flags, contour) != (40, feature, epoch, 0, 0):
            raise ValueError("selected cylinder is missing its linked planar cap")
        if curve.kind != 31 or curve.fields["radius"] != radius or curve.fields["normal"] != axis:
            raise ValueError("lateral rim is not the actual coaxial circle of the selected cylinder")
        caps.append((selector, contour))
        centres.append(curve.fields["centre"])
        delta = (value - start for value, start in zip(curve.fields["centre"], origin, strict=True))
        limits.append(fsum(value * normal for value, normal in zip(delta, axis, strict=True)))
        loop = member.fields["next"]
    if loop or caps != [(1, 0), (0, 0)] or limits[0] != 0.0 or not isclose(limits[1], child.PlanValue.DepthValue):
        raise ValueError("unsupported topology or axial cap extent")
    return CylinderFace(origin, axis, radius, tuple(centres), feature, creation, marker, tuple(caps),
                        side.fields["node_id"], tag, atom)


def make_feature_file(child):
    childfile = RequireNode(child.HeaderValue.FieldsValue["f38"], "moExtObject_c")
    return node("moExtObject_c", {
        **dict.fromkeys(("f48", "f4c", "f50", "f54", "f58", "f60", "f70", "f78"), 0),
        "refcfg": MakeFileConfig(child.SystemValue.RootValue, child.CurrentConfig),
        "shared": MakeSharedCopy(childfile),
    })


def make_face_ref(face, feature_file):
    def make_surface(name, **fields):
        keeper = node("moFR_c", {"f08": feature_file, "f10": {"f00": face.feature_id, "f08": face.creation}})
        return node(name, {"f10": {"f08": None, "f10": keeper}, **fields})

    side = make_surface("moFromSktEntSurfIdRep_c", f38=face.marker)
    rows = [{"f08": side}]
    for selector, contour in face.caps:
        rows.extend(({"f08": make_surface("moEndFaceSurfIdRep_c", f38=selector, f3c=contour)}, {"f08": None}))
    return node("moFaceRef_c", {
        "f60": 1, "f64": 0, "f08": len(rows), "fe8": 0x200, "f70": face.tag,
        "f28": 1e100, "f30": 1e100, "f40": None, "f10": rows, "f48": 0,
        "fd0": [], "nd0": 0, "fec": 19000, "has_f18": 0, "ff0": [], "nf0": 0,
    })


def make_facet(face):
    return node("moFacetedData_c", {
        "has_points": 0, "f40": face.node_id, "f50": face.body_atom,
        **dict.fromkeys(("f44", "f48", "f4c", "f54"), -1),
        "f14": 0,
        "f58_empty": 0, "f58": f"moFromSktEntSurfIdRep_c,{face.feature_id},{face.marker}, \n",
    })
