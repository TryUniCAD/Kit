from convert.adapters.solidworks.Archive.Construction.Blind.BlindZeroFields import (
    KBlindZeroFields,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.CheckColdDepth import (
    CheckColdDepth,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ReadColdDatum import (
    ReadColdDatum,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.Cold.ReadPatPrism import (
    ReadPatPrism,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.Cold.PatStock import (
    PatStock,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Patterns.PatternOwner import (
    PatternOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# both source contours use their own canonical front sketch and only a live forward depth
def ReadPatStocks(
    LinkValue: NativeLink, OwnerValue: PatternOwner
) -> tuple[PatStock, PatStock]:
    Features = IndexFeatures(LinkValue, PartPattern=True)
    (PlateNode,) = (
        Value
        for Value in Features.values()
        if Value.ClassValue.NameValue == "moExtrusion_c"
    )
    PlateValue = ReadExtrude(LinkValue, PlateNode, Features)
    SeedValue = ReadExtrude(LinkValue, OwnerValue.SeedValue, Features, JoinedSeed=True)
    (PlateFrame, PlateDatum), (SeedFrame, SeedDatum) = (
        ReadColdDatum(LinkValue, Value.ProfileValue, Features)
        for Value in (PlateValue, SeedValue)
    )
    if SeedFrame != PlateFrame or SeedDatum is not PlateDatum:
        raise ValueError(
            "cache free pattern sources require the same canonical Front plane"
        )
    for StockValue in (PlateValue, SeedValue):
        Fields = StockValue.EndValue.FieldsValue
        FromValue = RequireNative(Fields.get("f140"), "moFromEndSpec_c")
        if (
            StockValue.IsReversed
            or any(Fields.get(NameValue) != 0 for NameValue in KBlindZeroFields)
            or Fields.get("f08") != 1
            or Fields.get("f128") != 1
            or any(
                Fields.get(NameValue) is not None
                for NameValue in ("f20", "fc8", "fd0", "f138", "f90")
            )
            or Fields.get("fa0") != 0.0
            or FromValue.FieldsValue != {"t": 0}
            or not all(
                IsLineState(Fields.get(NameValue)) for NameValue in ("fe0", "f100")
            )
        ):
            raise ValueError(
                "cache free pattern sources require only one forward driving depth"
            )
        CheckColdDepth(LinkValue, StockValue)
    if PlateValue.DepthValue.Parameter is SeedValue.DepthValue.Parameter:
        raise ValueError("pattern plate and seed require distinct driving depths")
    return (
        ReadPatPrism(PlateValue, PlateFrame, LinkValue),
        ReadPatPrism(SeedValue, SeedFrame, LinkValue),
    )
