from collections.abc import Mapping
from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Assembly.Assembly import NativeAsm
from convert.adapters.solidworks.Assembly.NestedIndex.AsmMatrix import AsmMatrix
from convert.adapters.solidworks.Assembly.NestedIndex.IndexConflict import IndexConflict
from convert.adapters.solidworks.Assembly.NestedIndex.ReadNestedIndex import (
    ReadNestedIndex,
)
from convert.adapters.solidworks.Container.Container import (
    SldprtArchive,
    SldprtFormatError,
)
from interchange.Core.Common import FreezeMapping
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.document.Models.DocumentModel import CadDocument


# uncertain ownership must preserve the reader index projection without applying a partial hierarchy correction
def WithNestedIndex(
    Archive: SldprtArchive,
    Native: NativeAsm,
    DocumentIds: Mapping[int, str],
    Documents: Mapping[str, CadDocument],
    Definitions: tuple[ComponentDef, ...],
    Instances: tuple[ComponentInst, ...],
    *,
    Enabled: bool,
    Strict: bool,
    SourceKey: str,
    AllowFlat: bool = False,
) -> tuple[tuple[ComponentDef, ...], tuple[ComponentInst, ...], str | None]:
    if (
        not Enabled
        or Native.application_version != 19000
        or (
            not AllowFlat
            and not any(Value.depth > 0 for Value in Native.occurrence_paths)
        )
    ):
        return Definitions, Instances, None
    SourceData = {
        Identity: Documents[DocId].metadata.get(SourceKey)
        for Identity, DocId in DocumentIds.items()
    }
    try:
        Titles, Orders = ReadNestedIndex(Archive, Native, SourceData)
    except IndexConflict as ErrorInfo:
        if Strict:
            raise
        return Definitions, Instances, str(ErrorInfo)
    except (SldprtFormatError, ValueError, TypeError, KeyError) as ErrorInfo:
        if AllowFlat:
            if Strict:
                raise SldprtFormatError(
                    f"typed planar index rejected: {ErrorInfo}"
                ) from ErrorInfo
            return Definitions, Instances, str(ErrorInfo)
        return Definitions, Instances, None
    return (
        tuple(
            ReplaceValue(Value, name=Titles.get(NativeValue.object_id, Value.name))
            for Value, NativeValue in zip(Definitions, Native.definitions, strict=True)
        ),
        tuple(
            ReplaceValue(
                Value,
                order=OrderValue,
                transform=AsmMatrix(PoseValue),
                attributes=FreezeMapping(
                    {**Value.attributes, "typed_placement_m": PoseValue}
                ),
            )
            for Value, NativeValue in zip(Instances, Native.occurrences, strict=True)
            for OrderValue, PoseValue in (Orders[NativeValue.object_id],)
        ),
        None,
    )
