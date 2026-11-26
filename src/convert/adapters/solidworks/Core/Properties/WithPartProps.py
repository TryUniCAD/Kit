from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Properties.ApplyPartText import ApplyPartText
from convert.adapters.solidworks.Core.Properties.ReadPartText import ReadPartText
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumDocument import Severity
from interchange.Records.RecordDiagnostic import Diagnostic


# unsupported optional properties retain geometry and history while withholding every unqualified text projection
def WithPartProps(Document: CadDocument, Archive: SldprtArchive) -> CadDocument:
    if not any(
        NameValue in ("Contents/CusProps", "docProps/core.xml", "docProps/custom.xml")
        or NameValue.startswith("docProps/Config-")
        for NameValue in Archive.streams
    ):
        return Document
    try:
        PropsValue = ReadPartText(Document, Archive)
        return Document if PropsValue is None else ApplyPartText(Document, PropsValue)
    except (TypeError, ValueError, KeyError, SyntaxError) as ErrorInfo:
        Metadata = dict(Document.metadata)
        Metadata["solidworks.part_text_properties"] = {
            "status": "unsupported",
            "diagnostic": str(ErrorInfo),
            "profile": "compatible_literal_text",
        }
        DiagnosticValue = Diagnostic(
            code="solidworks.part_text_properties_unavailable",
            message=str(ErrorInfo),
            severity=Severity.INFO,
        )
        return ReplaceValue(
            Document,
            metadata=FreezeMapping(Metadata),
            diagnostics=Document.diagnostics + (DiagnosticValue,),
        )
