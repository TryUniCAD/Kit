from collections.abc import Mapping
from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# every planar carrier must still own exactly one of the six planes of the rectangular stock
def CheckFilletFace(
    NodesValue: Mapping[int, XmtNode],
    Bounds: tuple[tuple[float, float], ...],
) -> None:
    SeenValue: set[tuple[int, int]] = set()
    for NodeValue in NodesValue.values():
        if NodeValue.KindValue != 50:
            continue
        Normal = ReadXmtVector(NodeValue, "normal")
        Origin = ReadXmtVector(NodeValue, "pvec")
        (AxisIndex,) = tuple(
            Index for Index, AxisValue in enumerate(Normal) if AxisValue
        )
        if abs(Normal[AxisIndex]) != 1:
            raise ValueError("saved fillet retains a nonorthogonal stock carrier")
        (SideIndex,) = tuple(
            Index
            for Index, Coordinate in enumerate(Bounds[AxisIndex])
            if IsClose(Coordinate, Origin[AxisIndex], rel_tol=0.0, abs_tol=1e-11)
        )
        SeenValue.add((AxisIndex, SideIndex))
    if len(SeenValue) != 6:
        raise ValueError("saved fillet is missing a distinct rectangular stock plane")
