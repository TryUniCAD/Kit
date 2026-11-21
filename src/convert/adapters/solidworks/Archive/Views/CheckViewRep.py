from collections.abc import Mapping
from struct import pack as PackValue

from convert.adapters.solidworks.Archive.Views.MakeViewPair import MakeViewPair
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Archive.Views.ViewInput import ViewInput


# source affine and matrix presence state must be exactly representable by the semantic camera before regeneration
def CheckViewRep(
    ModelFields: Mapping[str, object],
    PanFields: Mapping[str, object],
    ViewValue: ViewInput,
) -> None:
    RebuiltValues = MakeViewPair(ViewValue)
    for SourceFields, RebuiltFields in zip(
        (ModelFields, PanFields), RebuiltValues, strict=True
    ):
        if set(SourceFields) != set(RebuiltFields):
            raise ValueError("source camera matrix presence cannot be regenerated")
        for FieldName in ("f58", "f60", "f68", "f70"):
            if PackValue("<d", RequireScalar(SourceFields[FieldName])) != PackValue(
                "<d", RequireScalar(RebuiltFields[FieldName])
            ):
                raise ValueError("source camera contains unrepresented affine state")
