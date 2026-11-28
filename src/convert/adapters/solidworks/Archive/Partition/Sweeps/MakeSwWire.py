from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakeBoundRoot import (
    KLocalLinearResolution,
    KLocalSessionPrecision,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakePrismNodes import (
    MakePrismNodes,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCell import PrismCell
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismRootKeys import (
    KPrismBody,
)
from convert.adapters.solidworks.Archive.Partition.Sweeps.SweepWireRefs import (
    SweepWireRefs,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from interchange.geometry.Models.GeometryCurves import ArcGeometry


# the path wire derives its supporting circle and exact trimmed endpoints from the signed front sketch arc
def WireSupports(
    RefsValue: SweepWireRefs, PathValue: ArcGeometry
) -> tuple[PrismCell, ...]:
    FrameValue = PrincipalFrame("z")
    RadiusValue = PathValue.Radius
    CenterValue = PathValue.Center
    return (
        PrismCell(
            KPrismBody,
            {
                "shell": RefsValue.ShellValue,
                "region": RefsValue.RegionValue,
                "edge": 0,
                "vertex": RefsValue.EndValue,
                "boundary_point": RefsValue.EndPoint,
                "boundary_curve": RefsValue.ArcValue,
                "boundary_surface": 0,
                "body_type": 2,
                "state": 1,
                "nom_geom_state": 1,
                "res_size": KLocalLinearResolution / KLocalSessionPrecision,
                "res_linear": KLocalLinearResolution,
            },
        ),
        PrismCell(
            RefsValue.RegionValue,
            {
                "body": KPrismBody,
                "next": 0,
                "previous": 0,
                "shell": RefsValue.ShellValue,
                "type": "V",
            },
        ),
        PrismCell(
            RefsValue.ShellValue,
            {
                "body": KPrismBody,
                "region": RefsValue.RegionValue,
                "face": 0,
                "front_face": 0,
                "edge": RefsValue.EdgeValue,
            },
        ),
        PrismCell(
            RefsValue.ArcValue,
            {
                "owner": RefsValue.EdgeValue,
                "previous": 0,
                "next": 0,
                "sense": "+",
                "centre": (CenterValue.XCoord, CenterValue.YCoord, 0.0),
                "normal": FrameValue.NormalValue,
                "x_axis": FrameValue.AxisU,
                "radius": RadiusValue,
            },
        ),
        PrismCell(
            RefsValue.EndPoint,
            {
                "owner": RefsValue.EndValue,
                "previous": 0,
                "next": RefsValue.StartPoint,
                "pvec": (RadiusValue, CenterValue.YCoord, 0.0),
            },
        ),
        PrismCell(
            RefsValue.StartPoint,
            {
                "owner": RefsValue.StartValue,
                "previous": RefsValue.EndPoint,
                "next": 0,
                "pvec": FrameValue.OriginValue,
            },
        ),
    )


# wire traversals retain explicit endpoints with no alternate face or adjacency ownership
def WireBoundary(RefsValue: SweepWireRefs) -> tuple[PrismCell, ...]:
    return (
        PrismCell(
            RefsValue.EndValue,
            {
                "halfedge": RefsValue.FirstFin,
                "previous": 0,
                "next": RefsValue.StartValue,
                "point": RefsValue.EndPoint,
                "owner": KPrismBody,
            },
        ),
        PrismCell(
            RefsValue.StartValue,
            {
                "halfedge": RefsValue.SecondFin,
                "previous": RefsValue.EndValue,
                "next": 0,
                "point": RefsValue.StartPoint,
                "owner": KPrismBody,
            },
        ),
        PrismCell(
            RefsValue.EdgeValue,
            {
                "halfedge": RefsValue.FirstFin,
                "previous": 0,
                "next": 0,
                "curve": RefsValue.ArcValue,
                "owner": RefsValue.ShellValue,
            },
        ),
        PrismCell(
            RefsValue.FirstFin,
            {
                "loop": 0,
                "forward": 0,
                "backward": 0,
                "vertex": RefsValue.EndValue,
                "other": RefsValue.SecondFin,
                "edge": RefsValue.EdgeValue,
                "next_at_vx": 0,
                "sense": "+",
            },
        ),
        PrismCell(
            RefsValue.SecondFin,
            {
                "loop": 0,
                "forward": 0,
                "backward": 0,
                "vertex": RefsValue.StartValue,
                "other": RefsValue.FirstFin,
                "edge": RefsValue.EdgeValue,
                "next_at_vx": 0,
                "sense": "-",
            },
        ),
    )


# the isolated path and its ghost binding share the current typed kernel node allocator
def MakeSwWire(PathValue: ArcGeometry) -> tuple[XmtNode, ...]:
    RefsValue = SweepWireRefs()
    return MakePrismNodes(
        (*WireSupports(RefsValue, PathValue), *WireBoundary(RefsValue))
    )
