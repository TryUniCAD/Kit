from __future__ import annotations

from types import MappingProxyType as FrozenMap
from typing import Callable as CallableType
from typing import cast as CastValue

from interchange.serialization.GetMapFields import GetMapFieldsMut
from interchange.serialization.MigrationRegistry import KMigrationRegistry
from interchange.serialization.RecordType import DataRecord, RecordCtor
from interchange.serialization.Wire import ResolveField
from interchange.serialization.WireData import KWireData


# record reconstruction applies migrations and mapping immutability before model construction
def DecodeRecordMut(
    SourceValue: dict[str, KWireData],
    TargetType: type[DataRecord],
    DecoderFunc: CallableType[
        [KWireData, dict[type[DataRecord], tuple[str, ...]]], object
    ],
    FieldCache: dict[type[DataRecord], tuple[str, ...]],
) -> object:
    WireArguments: dict[str, object] = {
        KeyValue: DecoderFunc(ItemValue, FieldCache)
        for KeyValue, ItemValue in SourceValue.items()
        if KeyValue != "$type"
    }
    MigrationFunc = KMigrationRegistry.get(TargetType)
    if MigrationFunc is not None:
        WireArguments = dict(MigrationFunc(FrozenMap(WireArguments)))
        FieldCache.clear()
    Arguments: dict[str, object] = {
        ResolveField(TargetType, KeyValue): ItemValue
        for KeyValue, ItemValue in WireArguments.items()
    }
    for FieldName in GetMapFieldsMut(TargetType, FieldCache):
        ArgumentValue = Arguments.get(FieldName)
        if isinstance(ArgumentValue, dict):
            MapValue = CastValue(dict[object, object], ArgumentValue)
            Arguments[FieldName] = FrozenMap(MapValue)
    RecordFactory = CastValue(RecordCtor, TargetType)
    return RecordFactory(**Arguments)
