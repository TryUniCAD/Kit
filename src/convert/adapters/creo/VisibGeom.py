from __future__ import annotations

from dataclasses import dataclass

from convert.adapters.creo.Stream import ReadCompactAt
from convert.adapters.creo.Stream import ScanFields
from convert.adapters.creo.Stream import StreamNode
from convert.adapters.creo.Stream import StreamParser

KPlaneType = 34
KPrototypeWindow = 12


@dataclass(frozen=True, slots=True)
class CreoSurface:
    geom_id: int
    geom_type: int
    feature_id: int | None
    envelope: tuple[float, ...]
    outline: tuple[float, ...]
    local_system: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class CreoCurve:
    curve_id: int
    curve_type: int
    feature_id: int | None
    points: tuple[float, ...]


def NumberValues(Value: object) -> tuple[float, ...]:
    if isinstance(Value, list):
        return tuple(
            float(Item) for Item in Value if isinstance(Item, (int, float))
        )
    return ()


def FindNumber(Nodes: list[StreamNode], Index: int, Name: str) -> int | None:
    for Node in Nodes[Index + 1 : Index + KPrototypeWindow]:
        if Node.name == Name and isinstance(Node.value, int):
            return Node.value
    return None


def FindValues(Nodes: list[StreamNode], Index: int, Name: str) -> tuple[float, ...]:
    for Node in Nodes[Index + 1 : Index + KPrototypeWindow]:
        if Node.name == Name:
            return NumberValues(Node.value)
    return ()


def ElementBoundaries(DataValue: bytes) -> dict[int, int]:
    Fields = ScanFields(DataValue)
    Names = [Field.name for Field in Fields]
    if "srf_array" not in Names or "crv_array" not in Names:
        return {}
    SrfIndex = Names.index("srf_array")
    CrvIndex = Names.index("crv_array")
    GeomIndex = next(
        Index
        for Index, Name in enumerate(Names)
        if Name == "geom_id" and Index > SrfIndex
    )
    CrvIdIndex = next(
        Index
        for Index, Name in enumerate(Names)
        if Name == "crv_id" and Index > CrvIndex
    )
    Boundaries: dict[int, int] = {}
    for OffsetValue in range(len(DataValue) - 1):
        if DataValue[OffsetValue] != 0xE3:
            continue
        _FeatureValue, AfterValue = ReadCompactAt(DataValue, OffsetValue + 1)
        if AfterValue <= OffsetValue + 1:
            continue
        if AfterValue + 1 < len(DataValue) and DataValue[AfterValue + 1] == 0x4A:
            Width = 1 if DataValue[OffsetValue + 1] <= 0x7F else 2
            SecondValue = DataValue[OffsetValue + 1 + Width]
            Boundaries[OffsetValue] = GeomIndex if SecondValue == 0x22 else CrvIdIndex
    return Boundaries


def ReadGeometry(
    DataValue: bytes,
) -> tuple[tuple[CreoSurface, ...], tuple[CreoCurve, ...]]:
    Nodes = StreamParser(DataValue, ElementBoundaries(DataValue)).Run()
    Surfaces: list[CreoSurface] = []
    Curves: list[CreoCurve] = []
    for Index, Node in enumerate(Nodes):
        if Node.name == "geom_id" and isinstance(Node.value, int):
            TypeValue = FindNumber(Nodes, Index, "geom_type")
            if TypeValue != KPlaneType:
                continue
            Surfaces.append(
                CreoSurface(
                    Node.value,
                    TypeValue,
                    FindNumber(Nodes, Index, "feat_id"),
                    FindValues(Nodes, Index, "envlp"),
                    FindValues(Nodes, Index, "outline"),
                    FindValues(Nodes, Index, "local_sys"),
                )
            )
        if Node.name == "crv_id" and isinstance(Node.value, int):
            Curves.append(
                CreoCurve(
                    Node.value,
                    FindNumber(Nodes, Index, "type") or 0,
                    FindNumber(Nodes, Index, "feat_id"),
                    FindValues(Nodes, Index, "crv_pnt_arr"),
                )
            )
    return tuple(Surfaces), tuple(Curves)
