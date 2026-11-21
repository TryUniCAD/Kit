from collections.abc import Mapping
from pathlib import Path as FilePath

from convert.adapters.solidworks.Assembly.Assembly import NativeAsm
from convert.adapters.solidworks.Container.Container import (
    SldprtArchive,
    SldprtFormatError,
)
from convert.adapters.solidworks.Core.TypedMates.CanReadMates import CanReadMates
from convert.adapters.solidworks.Core.TypedMates.PublicMateEnv import PublicMateEnv
from convert.adapters.solidworks.Core.TypedMates.ReadPublicMates import ReadPublicMates
from interchange import ComponentDocument, MateConstraint, MateEntity, MateGroup


# unqualified typed profiles must leave the established reader and its validation behavior available
def WithTypedMates(
    NativeValue: NativeAsm,
    Archive: SldprtArchive,
    PathsValue: Mapping[int, FilePath],
    DocumentIds: Mapping[int, str],
    Documents: tuple[ComponentDocument, ...],
    Entities: tuple[MateEntity, ...],
    RulesValue: tuple[MateConstraint, ...],
    GroupsValue: tuple[MateGroup, ...],
) -> tuple[
    tuple[MateEntity, ...],
    tuple[MateConstraint, ...],
    tuple[MateGroup, ...],
    Mapping[str, object] | None,
]:
    DocumentMap = {Value.id: Value.document for Value in Documents}
    EnvValue = PublicMateEnv(
        NativeValue,
        Archive,
        PathsValue,
        {
            Identity: DocumentMap[Value]
            for Identity, Value in DocumentIds.items()
            if Value in DocumentMap
        },
    )
    if not CanReadMates(EnvValue):
        return Entities, RulesValue, GroupsValue, None
    try:
        return ReadPublicMates(EnvValue, Entities, RulesValue, GroupsValue)
    except (OSError, ValueError, TypeError, KeyError) as ErrorInfo:
        if any(not Value.entity_ids for Value in RulesValue):
            raise SldprtFormatError(
                f"typed planar mate graph rejected: {ErrorInfo}"
            ) from ErrorInfo
        return (
            Entities,
            RulesValue,
            GroupsValue,
            {
                "status": "unsupported",
                "diagnostic": str(ErrorInfo),
                "full_selected_mate_graph": False,
                "public_writer_qualified": False,
            },
        )
