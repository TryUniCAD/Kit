from dataclasses import replace as ReplaceValue
from xml.etree.ElementTree import ParseError

from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Properties.ApplyPartText import ApplyPartText
from convert.adapters.solidworks.Core.Properties.ReadPartText import ReadPartText
from interchange import (
    CadDocument,
    Diagnostic,
    Severity,
    frozen_mapping as FrozenMapping,
)


# unsupported optional properties retain geometry and history while withholding every unqualified text projection
def WithPartProps(Document: CadDocument, Archive: SldprtArchive) -> CadDocument:
    if not any(
        NameValue in ("docProps/core.xml", "docProps/custom.xml", "Contents/CusProps")
        or NameValue.startswith("docProps/Config-")
        for NameValue in Archive.streams
    ):
        return Document
    try:
        return ApplyPartText(Document, ReadPartText(Document, Archive))
    except (TypeError, ValueError, KeyError, ParseError) as ErrorInfo:
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
            metadata=FrozenMapping(Metadata),
            diagnostics=Document.diagnostics + (DiagnosticValue,),
        )
