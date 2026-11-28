from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    DatumOffset,
    KDatumVector,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.CrossVector import (
    CrossVector,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.PrincDrive import (
    PrincDrive,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.SetPatPointMut import (
    SetPatPointMut,
)
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Patterns.Cold.ReadPatSeed import (
    ReadPatSeed,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.PatternOwner import (
    PatternOwner,
)


# live pitch and geometric display witnesses must agree with the actual signed seed geometry
def CheckPrPitch(OwnerValue: PatternOwner, Travel: KDatumVector) -> None:
    Pitch = OwnerValue.DriversValue[1]
    First = ReadPatSeed(OwnerValue.SeedValue)
    Normal = PrincipalFrame("z").NormalValue
    AxisNormal = CrossVector(Travel, Normal)
    FrameValue = PlaneFrame(First, Travel, CrossVector(AxisNormal, Travel), AxisNormal)
    ViewName = "*Left" if OwnerValue.DatumValue.ReversedValue else "*Top"
    Dimension = ArchiveNode(Pitch.DimensionValue.ClassValue, {})
    Expected: dict[str, object] = {}
    SetPatPointMut(
        Dimension,
        Expected,
        (First, DatumOffset(First, Travel, Pitch.LiveValue)),
        PrincDrive(FrameValue, Normal, ViewName),
    )
    DimFields = Pitch.DimensionValue.FieldsValue
    DisplayFields = Pitch.DisplayValue.FieldsValue
    if (
        any(
            DimFields.get(KeyValue) != Value
            for KeyValue, Value in Dimension.FieldsValue.items()
        )
        or DimFields.get("pt_flags") != 0
        or any(
            DisplayFields.get(KeyValue) != Value for KeyValue, Value in Expected.items()
        )
        or DisplayFields.get("f8b0") != 0.0
    ):
        raise ValueError(
            "cache free principal pitch does not match its actual witnesses and frame"
        )
