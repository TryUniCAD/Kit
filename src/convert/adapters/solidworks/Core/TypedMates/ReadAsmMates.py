from collections.abc import Mapping
from pathlib import Path as FilePath

from convert.adapters.solidworks.Assembly.Assembly import NativeAsm
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedMates.WithTypedMates import WithTypedMates
from interchange import (
    BrepPayload,
    ComponentDocument,
    Diagnostic,
    MateConstraint,
    MateEntity,
    MateGroup,
    Parameter,
    Severity,
)


# mate projection retains the previous payload and supplies validated live owners
def ReadAsmMates(
    Native: NativeAsm,
    Archive: SldprtArchive,
    ResolvedPaths: dict[int, FilePath],
    DocIds: dict[int, str],
    Documents: tuple[ComponentDocument, ...],
    Legacy: tuple[
        tuple[BrepPayload, ...],
        tuple[MateEntity, ...],
        tuple[MateConstraint, ...],
        tuple[MateGroup, ...],
    ],
    *,
    Strict: bool,
    ResolveComponents: bool,
    SourceKey: str,
) -> tuple[
    tuple[BrepPayload, ...],
    tuple[MateEntity, ...],
    tuple[MateConstraint, ...],
    tuple[MateGroup, ...],
    tuple[Parameter, ...],
    Mapping[str, object] | None,
]:
    Payloads, Entities, Rules, Groups = Legacy
    return (
        Payloads,
        *WithTypedMates(
            Native,
            Archive,
            ResolvedPaths,
            DocIds,
            Documents,
            Entities,
            Rules,
            Groups,
            Strict=Strict,
            ResolveComponents=ResolveComponents,
            SourceKey=SourceKey,
        ),
    )


# unsupported typed mates stay available in their raw archive with an explicit diagnostic
def AsmMateDiags(ReportValue: Mapping[str, object] | None) -> tuple[Diagnostic, ...]:
    if ReportValue is None or ReportValue.get("status") != "unsupported":
        return ()
    return (
        Diagnostic(
            code="sldasm.typed_mates_unqualified",
            message=str(ReportValue["diagnostic"]),
            severity=Severity.WARNING,
        ),
    )
