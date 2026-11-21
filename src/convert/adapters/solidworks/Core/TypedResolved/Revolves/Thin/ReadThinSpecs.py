from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.ReadThinDim import (
    ReadThinDim,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.ThinWallOwner import (
    ThinWallOwner,
)
from interchange.Features.ThinRevolve import KWallModes


# the thin spec keeps both wall display owners in the measured cold and saved states
def ReadThinSpecs(
    FeatureValue: ArchiveNode, *, IsSaved: bool = False
) -> tuple[str, ThinWallOwner, ThinWallOwner]:
    SpecValue = RequireNative(FeatureValue.FieldsValue.get("f8f0"), "moThinSpec_c")
    FieldsValue = SpecValue.FieldsValue
    ModeValue = FieldsValue.get("f28")
    if (
        type(ModeValue) is not int
        or not 0 <= ModeValue < len(KWallModes)
        or any(FieldsValue.get(NameValue) != 0 for NameValue in ("f2c", "f50", "f54"))
        or FieldsValue.get("f30") != (1e-7 if IsSaved else -2.0)
        or FieldsValue.get("f38") != -2.0
        or FieldsValue.get("f40") != 1
        or (not IsSaved and FieldsValue.get("f48") is not None)
    ):
        raise ValueError("SOLIDWORKS thin spec is outside its measured lifecycle state")
    FirstValue = ReadThinDim(FieldsValue.get("f08"), "D3", True)
    SecondValue = ReadThinDim(FieldsValue.get("f10"), "D4", ModeValue == 3)
    return KWallModes[ModeValue], FirstValue, SecondValue
