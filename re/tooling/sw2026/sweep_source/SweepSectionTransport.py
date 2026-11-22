from struct import pack

from convert.Geometry.Parasolid import EncodePartData, KTerminalFinSchema, ParaStream
from convert.adapters.solidworks.Archive.Construction.Circles.CircleInput import CircleInput
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import PrincipalFrame
from convert.adapters.solidworks.Archive.Partition.ImportHistory.WriteXmtEndMut import WriteXmtEndMut
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakeBoundRoot import (
    KLocalLinearResolution, KLocalSessionPrecision,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakePrismNodes import MakePrismNodes
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCell import PrismCell, PrismRef
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismRootKeys import KPrismBody
from convert.adapters.solidworks.Archive.Partition.LocalWrite.LocalXmtProfile import KLocalDescription, KLocalShapes
from convert.adapters.solidworks.Archive.Partition.LocalWrite.WriteXmtNodeMut import WriteXmtNodeMut
from SweepModel import require

KERNEL_FLAG = 0
PRESENT_BODY = 0


def make_section_cells(radius_metres):
    circle = CircleInput((0.0, 0.0), radius_metres, 19000)
    frame = PrincipalFrame("x")
    shell = PrismRef(13, "sheet")
    plane = PrismRef(50, "section-plane")
    boundary = PrismRef(31, "section-circle")
    region = PrismRef(19, "section-region")
    edge = PrismRef(16, "periodic-edge")
    face = PrismRef(14, "section-face")
    loop = PrismRef(15, "section-loop")
    fin = PrismRef(17, "loop-use")
    twin = PrismRef(17, "free-side-use")
    return (
        PrismCell(KPrismBody, {
            "shell": shell, "region": region, "edge": edge, "vertex": 0, "boundary_point": 0,
            "boundary_curve": boundary, "boundary_surface": plane,
            "res_size": KLocalLinearResolution / KLocalSessionPrecision,
            "res_linear": KLocalLinearResolution,
            "state": 1, "body_type": 3, "nom_geom_state": 1,
        }),
        PrismCell(region, {"body": KPrismBody, "next": 0, "previous": 0, "shell": shell, "type": "V"}),
        PrismCell(shell, {"body": KPrismBody, "region": region, "face": face, "front_face": face}),
        PrismCell(plane, {
            "owner": face, "previous": 0, "next": 0, "sense": "+",
            "pvec": frame.OriginValue, "normal": frame.NormalValue, "x_axis": frame.AxisU,
        }),
        PrismCell(boundary, {
            "owner": edge, "previous": 0, "next": 0, "sense": "+", "centre": frame.OriginValue,
            "normal": frame.NormalValue, "x_axis": frame.AxisU, "radius": circle.RadiusValue,
        }),
        PrismCell(edge, {
            "halfedge": fin, "previous": 0, "next": 0, "curve": boundary, "owner": KPrismBody,
        }),
        PrismCell(fin, {
            "loop": loop, "forward": fin, "backward": fin, "vertex": 0,
            "other": twin, "edge": edge, "next_at_vx": 0, "sense": "+",
        }),
        PrismCell(loop, {"face": face, "halfedge": fin}),
        PrismCell(twin, {
            "loop": 0, "forward": 0, "backward": 0, "vertex": 0,
            "other": fin, "edge": edge, "next_at_vx": 0, "sense": "-",
        }),
        PrismCell(face, {
            "loop": loop, "surface": plane, "shell": shell, "front_shell": shell, "previous": 0, "next": 0,
            "previous_front": 0, "next_front": 0, "sense": "+",
        }),
    )


def encode_section_nodes(nodes):
    body = bytearray(pack(">HI", 239, 0))
    schemas = set()
    for node in nodes:
        WriteXmtNodeMut(body, node, KLocalShapes[node.KindValue], schemas)
    WriteXmtEndMut(body)
    return ParaStream(bytes(body), KTerminalFinSchema, KLocalDescription)


def wrap_section(raw_transmit):
    compressed = EncodePartData(raw_transmit)
    return pack("<BiB", PRESENT_BODY, len(compressed) + 1, KERNEL_FLAG) + compressed


def make_section(radius_metres):
    require(type(radius_metres) in (int, float) and radius_metres > 0, "section radius must be positive")
    nodes = MakePrismNodes(make_section_cells(radius_metres))
    return encode_section_nodes(nodes)
