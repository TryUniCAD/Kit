from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# only the actual isolated external point row may be removed from contour incidence and retained as an origin datum
def ReadOriginPoint(
    RowValue: Mapping[str, object],
) -> tuple[Mapping[str, object], ArchiveNode, int, tuple[float, float]]:
    FieldsValue = NativeRecord(RowValue.get("point"))
    CreationId = FieldsValue.get("f0c")
    if (
        RowValue.get("kind") != 1
        or type(CreationId) is not int
        or CreationId <= 0
        or FieldsValue.get("f08") != 0
        or FieldsValue.get("f20") != 1
        or FieldsValue.get("fe4") != 6
        or FieldsValue.get("fe8") != 0
        or FieldsValue.get("pflags") != 30
        or FieldsValue.get("f54") != 4
        or any(
            FieldsValue.get(NameValue) is not None
            for NameValue in ("h1", "h2", "group")
        )
        or any(
            FieldsValue.get(NameValue) != 0
            for NameValue in ("f56", "has_name", "dflt", "fec", "has_jet", "ff0")
        )
    ):
        raise ValueError(
            "typed origin datum is not an isolated ordinary external point"
        )
    Position = NativeRecord(FieldsValue.get("pos"))
    Coordinates = RequireScalar(Position.get("x")), RequireScalar(Position.get("y"))
    if Coordinates != (0.0, 0.0):
        raise ValueError("typed origin datum has nonzero local coordinates")
    return (
        FieldsValue,
        RequireNative(FieldsValue.get("ext"), "sgExtEnt_c"),
        CreationId,
        Coordinates,
    )
