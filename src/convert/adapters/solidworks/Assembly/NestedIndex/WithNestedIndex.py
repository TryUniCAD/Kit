from collections.abc import Mapping
from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Assembly.Assembly import NativeAsm
from convert.adapters.solidworks.Assembly.NestedIndex.ReadNestedIndex import (
    ReadNestedIndex,
)
from convert.adapters.solidworks.Container.Container import (
    SldprtArchive,
    SldprtFormatError,
)
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentInstance import ComponentInst


# uncertain ownership must preserve the reader index projection without applying a partial hierarchy correction
def WithNestedIndex(
    Archive: SldprtArchive,
    Native: NativeAsm,
    SourceData: Mapping[int, object],
    Definitions: tuple[ComponentDef, ...],
    Instances: tuple[ComponentInst, ...],
) -> tuple[tuple[ComponentDef, ...], tuple[ComponentInst, ...]]:
    try:
        Titles, Orders = ReadNestedIndex(Archive, Native, SourceData)
    except (SldprtFormatError, ValueError, TypeError, KeyError):
        return Definitions, Instances
    return (
        tuple(
            ReplaceValue(Value, name=Titles.get(NativeValue.object_id, Value.name))
            for Value, NativeValue in zip(Definitions, Native.definitions, strict=True)
        ),
        tuple(
            ReplaceValue(Value, order=Orders[NativeValue.object_id])
            for Value, NativeValue in zip(Instances, Native.occurrences, strict=True)
        ),
    )
