from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.SegmentCodec.Features.Model.FieldValue import FieldValue


@MakeDataClass(frozen=True, slots=True)
class FeatureField:
    NameText: str
    Value: FieldValue
