from dataclasses import replace as Replace

from convert.adapters.freecad.Replay.AnnotateNative import AnnotateNative
from interchange.Records.RecordDiagnostic import Diagnostic
from interchange.document.Models.DocumentModel import CadDocument


# the historical fixture must supply its own digest without the compatibility reader
def PreLinkCarrier(Document: CadDocument) -> CadDocument:
    (Feature,) = Document.feature_timeline
    (LengthValue,) = (
        Param for Param in Document.parameters if Param.owner_id == Feature.id
    )
    Formula = LengthValue.expression
    assert Formula is not None and Formula.parameter_ids
    BeforeLinks = Replace(LengthValue, expression=Replace(Formula, parameter_ids=()))
    Finding = Diagnostic(
        "freecad.sheet_alias.unresolved",
        "Some native spreadsheet references remain unresolved",
        attributes={"counts": {"unsupported_reference": 1}},
    )
    return AnnotateNative(
        Replace(
            Document,
            parameters=tuple(
                BeforeLinks if Param is LengthValue else Param
                for Param in Document.parameters
            ),
            diagnostics=(*Document.diagnostics, Finding),
        )
    )
