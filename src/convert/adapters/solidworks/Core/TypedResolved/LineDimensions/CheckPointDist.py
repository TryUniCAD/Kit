from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckDimBase import (
    CheckDimBase,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord


# ordinary local point distances exclude transforms projection modes and nonpoint endpoint interpretation
def CheckPointDist(FieldsValue: Mapping[str, object]) -> None:
    CheckDimBase(FieldsValue)
    if (
        any(
            FieldsValue.get(NameValue) != 1
            for NameValue in ("f80", "f180", "f184", "f1b8")
        )
        or FieldsValue.get("f1bc") != 0
        or FieldsValue.get("fa0") != 0
        or FieldsValue.get("plane") is not None
    ):
        raise ValueError("typed rectangle distance has unsupported point geometry")
    Direction = NativeRecord(FieldsValue.get("dir"))
    if any(
        RequireScalar(Direction.get(NameValue)) != 0.0 for NameValue in ("x", "y", "z")
    ):
        raise ValueError("typed rectangle distance uses a projected direction")
    IdentityValue = FieldsValue.get("f50")
    if type(IdentityValue) is not int or IdentityValue < 0:
        raise ValueError("typed rectangle distance has no persistent identity")
