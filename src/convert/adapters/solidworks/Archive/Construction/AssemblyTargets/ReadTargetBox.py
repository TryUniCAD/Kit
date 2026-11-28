from math import isfinite as IsFinite
from convert.adapters.solidworks.Archive.Construction.PlanarMates.FieldRecord import (
    FieldRecord,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar


# parent bounds must consume the actual generated assembly local box rather than substitute aggregate extrema for its independent sphere
def ReadTargetBox(RootValue: ArchiveNode) -> dict[str, float]:
    if (
        RootValue.ClassValue.NameValue != "moAssembly_c"
        or RootValue.FieldsValue.get("has_f1a18") != 1
    ):
        raise ValueError("a generated subassembly requires its actual local bounds")
    FieldsValue = FieldRecord(RootValue.FieldsValue["f1a18"])
    ResultValue = {
        f"b{IndexValue}": RequireScalar(FieldsValue[f"b{IndexValue}"])
        for IndexValue in range(10)
    }
    if not all(IsFinite(NumberValue) for NumberValue in ResultValue.values()):
        raise ValueError("generated subassembly bounds must remain finite")
    return ResultValue
