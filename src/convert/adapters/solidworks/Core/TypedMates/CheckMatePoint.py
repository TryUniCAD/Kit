from math import isclose as IsClose
from pathlib import PureWindowsPath

from convert.adapters.solidworks.Assembly.PlanarMates.PlanarEndpoint import (
    PlanarEndpoint,
)
from convert.adapters.solidworks.Assembly.PlanarMates.ReadPlane import ReadVector
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireNode
from convert.adapters.solidworks.Assembly.PlanarMates.PlanarContext import PlanarContext
from convert.adapters.solidworks.Core.TypedMates.ReadMateFrame import ReadMateFrame


# a matching identity stamp must not hide a stale or contradictory cached plane geometry
def CheckMatePoint(Endpoint: PlanarEndpoint, Context: PlanarContext) -> None:
    ItemValue = Context.OccurrenceMap[Endpoint.OccurrenceFeatureId]
    Definition = Context.DefinitionMap[Endpoint.ChildDefinitionId]
    ChildKey = (
        PureWindowsPath(Definition.source_path).name.casefold(),
        Endpoint.ChildConfigId,
    )
    DatumValue = Context.ChildMap[ChildKey].DatumNodes[Endpoint.DatumFeatureId]
    PlaneValue = RequireNode(
        DatumValue.FieldsValue.get("f6f8"), "moDefaultRefPlnData_c"
    )
    Origin = ReadVector(PlaneValue.FieldsValue.get("root"))
    Normal = ReadVector(PlaneValue.FieldsValue.get("normal"))
    Matrix = ReadMateFrame(ItemValue.transform)
    ExpectedRoot = tuple(
        sum(Origin[AxisIndex] * Matrix[AxisIndex * 4 + Index] for AxisIndex in range(3))
        + Matrix[12 + Index]
        for Index in range(3)
    )
    ExpectedNorm = tuple(
        sum(Normal[AxisIndex] * Matrix[AxisIndex * 4 + Index] for AxisIndex in range(3))
        for Index in range(3)
    )
    if not all(
        IsClose(Actual, Expected, rel_tol=1e-10, abs_tol=1e-12)
        for Actual, Expected in zip(
            (*Endpoint.OriginValue, *Endpoint.NormalValue),
            (*ExpectedRoot, *ExpectedNorm),
            strict=True,
        )
    ):
        raise ValueError(
            "typed mate wrapper plane disagrees with its actual child and occurrence"
        )
