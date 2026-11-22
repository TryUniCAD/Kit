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
from convert.adapters.solidworks.Archive.Partition.Sweeps.SweepSheetRefs import (
    SweepSheetRefs,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector


# the section materializes a right planar support and full periodic boundary from the same authored circle
def SheetSupports(
    RefsValue: SweepSheetRefs, RadiusValue: float
) -> tuple[PrismCell, ...]:
    FrameValue = PrincipalFrame("x")
    return (
        PrismCell(
            KPrismBody,
            {
                "shell": RefsValue.ShellValue,
                "region": RefsValue.RegionValue,
                "edge": RefsValue.EdgeValue,
                "vertex": 0,
                "boundary_point": 0,
                "boundary_curve": RefsValue.ArcValue,
                "boundary_surface": RefsValue.PlaneValue,
                "res_size": KLocalLinearResolution / KLocalSessionPrecision,
                "res_linear": KLocalLinearResolution,
                "state": 1,
                "body_type": 3,
                "nom_geom_state": 1,
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
                "face": RefsValue.FaceValue,
                "front_face": RefsValue.FaceValue,
            },
        ),
        PrismCell(
            RefsValue.PlaneValue,
            {
                "owner": RefsValue.FaceValue,
                "previous": 0,
                "next": 0,
                "sense": "+",
                "pvec": FrameValue.OriginValue,
                "normal": FrameValue.NormalValue,
                "x_axis": FrameValue.AxisU,
            },
        ),
        PrismCell(
            RefsValue.ArcValue,
            {
                "owner": RefsValue.EdgeValue,
                "previous": 0,
                "next": 0,
                "sense": "+",
                "centre": FrameValue.OriginValue,
                "normal": FrameValue.NormalValue,
                "x_axis": FrameValue.AxisU,
                "radius": RadiusValue,
            },
        ),
    )


# a closed swept section has no kernel vertex and only its positive fin belongs to the face loop
def SheetBoundary(RefsValue: SweepSheetRefs) -> tuple[PrismCell, ...]:
    return (
        PrismCell(
            RefsValue.EdgeValue,
            {
                "halfedge": RefsValue.FirstFin,
                "previous": 0,
                "next": 0,
                "curve": RefsValue.ArcValue,
                "owner": KPrismBody,
            },
        ),
        PrismCell(
            RefsValue.FirstFin,
            {
                "loop": RefsValue.LoopValue,
                "forward": RefsValue.FirstFin,
                "backward": RefsValue.FirstFin,
                "vertex": 0,
                "other": RefsValue.SecondFin,
                "edge": RefsValue.EdgeValue,
                "next_at_vx": 0,
                "sense": "+",
            },
        ),
        PrismCell(
            RefsValue.LoopValue,
            {"face": RefsValue.FaceValue, "halfedge": RefsValue.FirstFin},
        ),
        PrismCell(
            RefsValue.SecondFin,
            {
                "loop": 0,
                "forward": 0,
                "backward": 0,
                "vertex": 0,
                "other": RefsValue.FirstFin,
                "edge": RefsValue.EdgeValue,
                "next_at_vx": 0,
                "sense": "-",
            },
        ),
        PrismCell(
            RefsValue.FaceValue,
            {
                "loop": RefsValue.LoopValue,
                "surface": RefsValue.PlaneValue,
                "shell": RefsValue.ShellValue,
                "front_shell": RefsValue.ShellValue,
                "previous": 0,
                "next": 0,
                "previous_front": 0,
                "next_front": 0,
                "sense": "+",
            },
        ),
    )


# the section kernel graph is rebuilt from the same editable circle as the native sketch
def MakeSwSheet(CircleValue: CircleGeometry) -> tuple[XmtNode, ...]:
    if (
        type(CircleValue) is not CircleGeometry
        or CircleValue.Center != PlaneVector(0.0, 0.0)
        or type(CircleValue.Radius) not in (int, float)
        or not 0.001 <= CircleValue.Radius < 0.15
    ):
        raise ValueError("sweep section requires the canonical positive right circle")
    RefsValue = SweepSheetRefs()
    return MakePrismNodes(
        (*SheetSupports(RefsValue, CircleValue.Radius), *SheetBoundary(RefsValue))
    )
