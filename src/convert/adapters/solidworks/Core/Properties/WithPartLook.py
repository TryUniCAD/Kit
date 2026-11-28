from dataclasses import replace as ReplaceValue

from convert.adapters.base.Materials.CheckPartLook import KPartLookKey
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Properties.ReadPartLook import ReadPartLook
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumDocument import Severity
from interchange.Records.RecordDiagnostic import Diagnostic


# explicit inspection records why unsupported source appearance could not be projected
def PartLookError(Document: CadDocument, Reason: str) -> CadDocument:
    Notice = Diagnostic(
        code="solidworks.part_visual_unavailable",
        message=Reason,
        severity=Severity.INFO,
    )
    return ReplaceValue(
        Document,
        metadata=FreezeMapping(
            {**Document.metadata, KPartLookKey: {"status": "unsupported", "diagnostic": Reason}}
        ),
        diagnostics=Document.diagnostics + (Notice,),
    )


# optional inspection preserves the default read and exposes unsupported source layouts on request
def WithPartLook(
    Document: CadDocument,
    Archive: SldprtArchive,
    ActiveConfigId: int | None,
    Requested: bool,
) -> CadDocument:
    if not Requested:
        return Document
    if ActiveConfigId != 0:
        return PartLookError(Document, "stored appearance requires active configuration 0")
    if Archive.format_version != 4 or Archive.get("Contents/Config-0") is None:
        return PartLookError(Document, "stored appearance requires a format-4 Config-0 stream")
    try:
        Evidence = ReadPartLook(Archive)
    except (TypeError, ValueError, KeyError, SyntaxError) as ErrorInfo:
        return PartLookError(Document, str(ErrorInfo))
    return ReplaceValue(
        Document,
        metadata=FreezeMapping({**Document.metadata, KPartLookKey: Evidence}),
    )
