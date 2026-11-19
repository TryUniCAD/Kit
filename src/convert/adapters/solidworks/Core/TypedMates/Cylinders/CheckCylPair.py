from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Construction.Geometry.DotVector import (
    DotVector,
)
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CylEndpoint import (
    CylEndpoint,
)


# solved concentric semantics require independent coaxial geometry as well as the serialized alignment choice
def CheckCylPair(Endpoints: tuple[CylEndpoint, ...], AlignCode: int) -> None:
    FirstValue, SecondValue = Endpoints
    if (
        FirstValue.ItemValue.feature_id == SecondValue.ItemValue.feature_id
        or FirstValue.ItemValue.definition_id != SecondValue.ItemValue.definition_id
    ):
        raise ValueError(
            "concentric mate requires distinct occurrences of the same actual child"
        )
    if DotVector(FirstValue.LocalAxisValue, SecondValue.LocalAxisValue) <= 0.0:
        raise ValueError(
            "concentric wrappers disagree on the direction of the same child cylinder"
        )
    ProductValue = DotVector(FirstValue.AxisValue, SecondValue.AxisValue)
    OffsetValue = tuple(
        SecondValue.OriginValue[Index] - FirstValue.OriginValue[Index]
        for Index in range(3)
    )
    SlideValue = sum(
        OffsetValue[Index] * FirstValue.AxisValue[Index] for Index in range(3)
    )
    Residual = sum(
        (OffsetValue[Index] - SlideValue * FirstValue.AxisValue[Index]) ** 2
        for Index in range(3)
    )
    if (
        not IsClose(
            ProductValue, 1.0 if AlignCode == 1 else -1.0, rel_tol=0.0, abs_tol=1e-10
        )
        or Residual > 1e-20
    ):
        raise ValueError(
            "concentric cylinders disagree with the solved coaxial alignment"
        )
