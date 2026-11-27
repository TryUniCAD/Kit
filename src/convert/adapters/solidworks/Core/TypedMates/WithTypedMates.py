from collections.abc import Mapping
from pathlib import Path as FilePath

from convert.adapters.solidworks.Assembly.Assembly import NativeAsm
from convert.adapters.solidworks.Container.Container import (
    SldprtArchive,
    SldprtFormatError,
)
from convert.adapters.solidworks.Core.TypedMates.CanReadMates import (
    CanReadMates,
    HasPlanarMates,
)
from convert.adapters.solidworks.Core.TypedMates.PublicMateEnv import PublicMateEnv
from convert.adapters.solidworks.Core.TypedMates.ReadPublicMates import ReadPublicMates
from interchange import (
    ComponentDocument,
    MateConstraint,
    MateEntity,
    MateGroup,
    Parameter,
)


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
    *,
    Strict: bool,
    ResolveComponents: bool,
    SourceKey: str,
) -> tuple[
    tuple[MateEntity, ...],
    tuple[MateConstraint, ...],
    tuple[MateGroup, ...],
    tuple[Parameter, ...],
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
        SourceKey,
    )
    Deferred = not ResolveComponents and HasPlanarMates(EnvValue)
    if not Deferred and not CanReadMates(EnvValue):
        if Strict and HasPlanarMates(EnvValue):
            raise SldprtFormatError(
                "typed planar mate graph requires two qualified component occurrences"
            )
        return Entities, RulesValue, GroupsValue, (), None
    try:
        return ReadPublicMates(
            EnvValue, Entities, RulesValue, GroupsValue, Deferred=Deferred
        )
    except (OSError, ValueError, TypeError, KeyError) as ErrorInfo:
        if Strict:
            raise SldprtFormatError(
                f"typed planar mate graph rejected: {ErrorInfo}"
            ) from ErrorInfo
        return (
            (),
            (),
            (),
            (),
            {
                "status": "unsupported",
                "diagnostic": str(ErrorInfo),
                "full_selected_mate_graph": False,
                "public_writer_qualified": False,
            },
        )
