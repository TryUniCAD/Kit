from collections.abc import Mapping
from pathlib import Path as FilePath

from convert.adapters.solidworks.Assembly.Assembly import NativeAsm
from convert.adapters.solidworks.Container.Container import (
    SldprtArchive,
    SldprtFormatError,
)
from convert.adapters.solidworks.Core.TypedMates.CanReadMates import CanReadMates
from convert.adapters.solidworks.Core.TypedMates.Cold.CheckColdShape import (
    CheckColdShape,
)
from convert.adapters.solidworks.Core.TypedMates.Cold.IsColdPair import IsColdPair
from convert.adapters.solidworks.Core.TypedMates.Cold.IsColdMateSet import (
    IsColdMateSet,
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
    PerpValue = IsColdPair(NativeValue, Archive, ("moMatePerpendicular",))
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
        ColdPerp=PerpValue,
    )
    ColdValue = IsColdMateSet(NativeValue, Archive)
    PairValue = IsColdPair(NativeValue, Archive)
    MustBind = ColdValue or PairValue or PerpValue
    try:
        if MustBind:
            CheckColdShape(NativeValue)
            if not ResolveComponents:
                return (
                    (),
                    (),
                    (),
                    (),
                    {
                        "status": "deferred",
                        "full_selected_mate_graph": False,
                        "public_writer_qualified": False,
                    },
                )
        if not CanReadMates(EnvValue):
            if MustBind:
                raise ValueError(
                    "cold planar mate graph requires its actual linked part"
                )
            return Entities, RulesValue, GroupsValue, (), None
        return ReadPublicMates(
            EnvValue,
            Entities,
            RulesValue,
            GroupsValue,
            ColdRequired=ColdValue,
            MeasuredPair=PairValue,
        )
    except (OSError, ValueError, TypeError, KeyError) as ErrorInfo:
        if (MustBind and Strict) or (
            not MustBind and any(not Value.entity_ids for Value in RulesValue)
        ):
            raise SldprtFormatError(
                f"typed planar mate graph rejected: {ErrorInfo}"
            ) from ErrorInfo
        return (
            () if MustBind else Entities,
            () if MustBind else RulesValue,
            () if MustBind else GroupsValue,
            (),
            {
                "status": "unsupported",
                "diagnostic": str(ErrorInfo),
                "full_selected_mate_graph": False,
                "public_writer_qualified": False,
            },
        )
