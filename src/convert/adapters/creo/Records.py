from __future__ import annotations

from dataclasses import dataclass

from interchange.core.Common import FreezeMapping
from interchange.enums.EnumFeatures import FeatureKind
from interchange.features.FeatureStep import FeatureStep
from interchange.records.RecordProvenance import Provenance
from interchange.records.RecordProvenance import ProvenanceSpan

from convert.adapters.creo.Format import KFormatId

KFeatureIdHeader = b"\xe0\x01id\x00"
KFeatureAnchor = b"\xe3\xf6"
KAnchorWindow = 16
KMinimumRowBytes = 16

KFeatureClassLabel = {
    911: "hole",
    913: "round",
    914: "chamfer",
    916: "cut",
    917: "protrusion",
    923: "datum_plane",
    926: "section",
    927: "draft",
    942: "surface",
    946: "surface_merge",
    979: "coordinate_system",
}


@dataclass(frozen=True, slots=True)
class CreoFeatureRow:
    feature_id: int
    root_class: int | None
    offset: int
    length: int


def ReadCompactAt(DataValue: bytes, Position: int) -> tuple[int | None, int]:
    if Position >= len(DataValue):
        return None, Position
    FirstValue = DataValue[Position]
    if FirstValue <= 0x7F:
        return FirstValue, Position + 1
    if FirstValue <= 0xBF:
        if Position + 1 >= len(DataValue):
            return None, Position
        return ((FirstValue & 0x3F) << 8) | DataValue[Position + 1], Position + 2
    if FirstValue <= 0xDF:
        if Position + 2 >= len(DataValue):
            return None, Position
        return (
            ((FirstValue & 0x1F) << 16)
            | (DataValue[Position + 1] << 8)
            | DataValue[Position + 2],
            Position + 3,
        )
    return None, Position


def RootClassAt(DataValue: bytes, Position: int, Limit: int) -> int | None:
    EndValue = min(Limit, len(DataValue))
    AnchorValue = DataValue.find(KFeatureAnchor, Position, EndValue)
    while AnchorValue >= 0:
        ClassValue, AfterValue = ReadCompactAt(DataValue, AnchorValue + 2)
        if (
            ClassValue is not None
            and AfterValue < len(DataValue)
            and DataValue[AfterValue] == 0xE1
        ):
            return ClassValue
        AnchorValue = DataValue.find(KFeatureAnchor, AnchorValue + 1, EndValue)
    return None


def BoundaryStarts(DataValue: bytes) -> list[tuple[int, int, int]]:
    Starts: list[tuple[int, int, int]] = []
    for OffsetValue in range(len(DataValue)):
        if OffsetValue != 0 and DataValue[OffsetValue - 1] != 0xE3:
            continue
        FeatureValue, AfterValue = ReadCompactAt(DataValue, OffsetValue)
        if FeatureValue is None or FeatureValue <= 0:
            continue
        ClassValue = RootClassAt(DataValue, AfterValue, AfterValue + KAnchorWindow)
        if ClassValue is None or ClassValue not in KFeatureClassLabel:
            continue
        Starts.append((OffsetValue, FeatureValue, ClassValue))
    return Starts


def DefinitionStarts(DataValue: bytes) -> list[tuple[int, int]]:
    Starts: list[tuple[int, int]] = []
    Position = DataValue.find(KFeatureIdHeader)
    while Position >= 0:
        FeatureValue, _AfterValue = ReadCompactAt(
            DataValue, Position + len(KFeatureIdHeader)
        )
        if FeatureValue is not None and FeatureValue > 0:
            Starts.append((Position, FeatureValue))
        Position = DataValue.find(KFeatureIdHeader, Position + 1)
    return Starts


def ReadFeatureRows(DataValue: bytes) -> tuple[CreoFeatureRow, ...]:
    Starts = BoundaryStarts(DataValue)
    Rows: list[CreoFeatureRow] = []
    SeenIds: set[int] = set()
    for IndexValue, (StartValue, FeatureValue, ClassValue) in enumerate(Starts):
        if IndexValue + 1 < len(Starts):
            EndValue = Starts[IndexValue + 1][0]
        else:
            EndValue = len(DataValue)
        LengthValue = EndValue - StartValue
        if LengthValue < KMinimumRowBytes or FeatureValue in SeenIds:
            continue
        SeenIds.add(FeatureValue)
        Rows.append(
            CreoFeatureRow(FeatureValue, ClassValue, StartValue, LengthValue)
        )
    for Position, FeatureValue in DefinitionStarts(DataValue):
        if FeatureValue in SeenIds:
            continue
        SeenIds.add(FeatureValue)
        EndValue = next(
            (Start for Start, _Id, _Class in Starts if Start > Position),
            len(DataValue),
        )
        Rows.append(
            CreoFeatureRow(FeatureValue, None, Position, EndValue - Position)
        )
    Rows.sort(key=lambda RowValue: RowValue.offset)
    return tuple(Rows)


def FeatureSteps(
    Rows: tuple[CreoFeatureRow, ...], SectionName: str = "AllFeatur"
) -> tuple[FeatureStep, ...]:
    Steps: list[FeatureStep] = []
    for IndexValue, Row in enumerate(Rows):
        ClassValue = Row.root_class
        if ClassValue is None:
            LabelValue = "unknown"
        else:
            LabelValue = KFeatureClassLabel.get(ClassValue, "unknown")
        Steps.append(
            FeatureStep(
                id=f"creo:feature:{Row.feature_id}",
                name=f"Creo {LabelValue} {Row.feature_id}",
                kind=FeatureKind.NATIVE,
                order=IndexValue,
                provenance=Provenance(
                    KFormatId,
                    str(Row.feature_id),
                    spans=(
                        ProvenanceSpan(
                            SectionName, Row.offset, Row.length, "feature_row"
                        ),
                    ),
                ),
                attributes=FreezeMapping(
                    {
                        "creo.feature_id": Row.feature_id,
                        "creo.root_class": ClassValue,
                        "creo.root_class_label": LabelValue,
                    }
                ),
            )
        )
    return tuple(Steps)
