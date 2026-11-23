from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    KDatumVector,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the original sketch preserves the exact metre coordinates before neutral unit conversion
def ReadPatSeed(SeedValue: ArchiveNode) -> KDatumVector:
    (ProfileValue,) = ReadParents(SeedValue)
    Sketch = RequireNative(ProfileValue.FieldsValue.get("pd_f80"), "sgSketch")
    Points = NativeRows(Sketch.FieldsValue.get("points"))
    if len(Points) != 4 or any(Value.get("kind") != 0 for Value in Points):
        raise ValueError("cache free principal pitch requires its actual seed corners")
    Positions = tuple(
        NativeRecord(NativeRecord(Value.get("point")).get("pos")) for Value in Points
    )
    First = tuple(RequireScalar(Positions[0].get(KeyValue)) for KeyValue in ("x", "y"))
    if any(
        First[Index] != min(RequireScalar(Value.get(KeyValue)) for Value in Positions)
        for Index, KeyValue in enumerate(("x", "y"))
    ):
        raise ValueError(
            "cache free principal pitch requires the actual first seed corner"
        )
    return (First[0], First[1], 0.0)
