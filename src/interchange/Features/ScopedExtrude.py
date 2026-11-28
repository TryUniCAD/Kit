from dataclasses import dataclass as MakeDataClass
from sys import float_info as FloatLimits
from typing import Literal, cast as CastValue

from interchange.Enums.EnumValues import ValueKind
from interchange.Features.DistanceParam import KLengthFactors
from interchange.Features.FeatureContract import FeatureDef
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature


# empty selected scope has meaning only for an ordinary forward finite extrusion
def CheckFirstMode(Definition: ExtrudeFeature) -> None:
    LengthValue = Definition.length
    if LengthValue is None or LengthValue.kind != ValueKind.KLength:
        raise ValueError("first creator scope requires a positive finite length")
    Number = LengthValue.value
    Factor = KLengthFactors.get(LengthValue.unit)
    if (
        not isinstance(Number, (int, float))
        or isinstance(Number, bool)
        or Factor is None
        or not 0 < Number <= FloatLimits.max / max(Factor, 1.0)
    ):
        raise ValueError("first creator scope requires a positive finite length")
    if (
        Definition.end_condition != ExtrudeEnd.KBlind
        or Definition.reversed is not False
        or Definition.symmetric is not False
        or Definition.up_to_reference != ""
        or Definition.second_up_to_reference != ""
        or any(
            ValueItem is not None
            for ValueItem in (
                Definition.offset,
                Definition.draft_angle,
                Definition.second_length,
                Definition.second_end_condition,
                Definition.second_offset,
                Definition.second_draft_angle,
            )
        )
    ):
        raise ValueError("first creator scope requires one ordinary forward blind end")


# scoped features preserve authored selection independently of the result at this rebuild
@MakeDataClass(frozen=True, slots=True)
class ScopedExtrude(FeatureDef):
    Extrusion: ExtrudeFeature
    ScopeMode: Literal["all_applicable", "explicit", "first_creator"]
    SelectedBodyIds: tuple[str, ...]
    AffectedBodyIds: tuple[str, ...]

    # malformed scope records must fail before a writer can mistake them for an ordinary extrusion
    def __post_init__(self) -> None:
        if not isinstance(CastValue(object, self.Extrusion), ExtrudeFeature):
            raise ValueError("scoped extrusion requires an extrusion definition")
        for BodyIds in (self.SelectedBodyIds, self.AffectedBodyIds):
            if not isinstance(CastValue(object, BodyIds), tuple) or not all(
                isinstance(CastValue(object, Identity), str) and Identity.strip()
                for Identity in BodyIds
            ):
                raise ValueError("scope body IDs must be a tuple of nonempty text")
            if len(set(BodyIds)) != len(BodyIds):
                raise ValueError("scope body IDs must be distinct within each list")
        ScopeMode = CastValue(object, self.ScopeMode)
        if ScopeMode == "all_applicable":
            if self.SelectedBodyIds:
                raise ValueError("all-applicable scope cannot carry explicit body IDs")
        elif ScopeMode == "first_creator":
            if self.SelectedBodyIds or self.AffectedBodyIds:
                raise ValueError("first creator scope requires empty prior body lists")
            CheckFirstMode(self.Extrusion)
        elif ScopeMode != "explicit" or not self.SelectedBodyIds:
            raise ValueError("explicit scope requires selected body IDs")
        elif not set(self.AffectedBodyIds) <= set(self.SelectedBodyIds):
            raise ValueError("explicit scope affected bodies must be selected")
