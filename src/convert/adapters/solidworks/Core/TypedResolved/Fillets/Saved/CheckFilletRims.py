from collections.abc import Mapping
from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# the two typed circular carriers must terminate the same actual rounded cylinder
def CheckFilletRims(
    NodesValue: Mapping[int, XmtNode],
    Origin: tuple[float, float, float],
    Bounds: tuple[tuple[float, float], ...],
    AxisIndex: int,
    Radius: float,
) -> None:
    AxialStations: list[float] = []
    for NodeValue in NodesValue.values():
        if NodeValue.KindValue != 31:
            continue
        Center = ReadXmtVector(NodeValue, "centre")
        Normal = ReadXmtVector(NodeValue, "normal")
        CrossAxes = tuple(Index for Index in range(3) if Index != AxisIndex)
        if (
            NodeValue.FieldsValue.get("radius") != Radius
            or abs(Normal[AxisIndex]) != 1
            or any(
                Normal[Index] != 0
                or not IsClose(Center[Index], Origin[Index], rel_tol=0.0, abs_tol=1e-11)
                for Index in CrossAxes
            )
        ):
            raise ValueError("saved fillet cap rim does not agree with its cylinder")
        AxialStations.append(Center[AxisIndex])
    if len(AxialStations) != 2 or not all(
        IsClose(Actual, Boundary, rel_tol=0.0, abs_tol=1e-11)
        for Actual, Boundary in zip(
            sorted(AxialStations), Bounds[AxisIndex], strict=True
        )
    ):
        raise ValueError("saved fillet cap rims miss the actual stock endpoints")
