from convert.adapters.solidworks.Archive.Construction.Patterns.Direction.ReadPatDir import (
    ReadPatDir,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Direction.ReadPatFrame import (
    ReadPatPoint,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Patterns.Cold.CheckPrPitch import (
    CheckPrPitch,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.Cold.CheckPrViews import (
    CheckPrViews,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.PatternOwner import (
    PatternOwner,
)


# cold principal geometry requires the actual plane line and matching driver presentation from one archive
def CheckPrincPat(LinkValue: NativeLink, OwnerValue: PatternOwner) -> None:
    Datum = OwnerValue.DatumValue
    Expected = ReadPatDir(Datum.PlaneValue)
    Fields = Datum.LineValue.FieldsValue
    Reversed = Datum.ReversedValue
    if (
        (Expected.RoleValue, Reversed) not in ((1, False), (2, True))
        or Fields.get("f68") != 1
        or Fields.get("f0c") != 0
        or Fields.get("fb0") != 0.0
        or Fields.get("fb8") != Expected.SpanValue
        or ReadPatPoint(Fields.get("fc8")) != Expected.PointValue
        or ReadPatPoint(Fields.get("fe0")) != Expected.DirectionValue
    ):
        raise ValueError(
            "cache free principal pattern requires its actual signed datum line"
        )
    Travel = Expected.DirectionValue
    Signed = (-Travel[0], -Travel[1], -Travel[2]) if Reversed else Travel
    CheckPrViews(LinkValue, OwnerValue.DriversValue, Reversed)
    CheckPrPitch(OwnerValue, Signed)
