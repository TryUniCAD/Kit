from dataclasses import replace as ReplaceValue

from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Equations.BindSavedEq import (
    BindSavedEq,
)
from convert.adapters.solidworks.Core.TypedResolved.Equations.StripEqGeom import (
    StripEqGeom,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumDocument import Severity
from interchange.Records.RecordDiagnostic import Diagnostic


# both read modes validate the actual saved partition before they publish body ownership
def ReadSavedEq(
    Document: CadDocument,
    Archive: SldprtArchive,
    Model: NativeModel,
    Settings: ReadOptions,
) -> CadDocument:
    Relation = Model.WidthDepth
    if Relation is None or Relation.SourceValue is not Archive:
        raise SldprtFormat(
            "saved width-depth body requires its own typed local relation"
        )
    try:
        Bound = BindSavedEq(Document, Model, Relation)
    except (KeyError, TypeError, ValueError, OverflowError) as ErrorValue:
        if Settings.strict:
            raise SldprtFormat(
                f"SOLIDWORKS saved width-depth body is unqualified: {ErrorValue}"
            ) from ErrorValue
        Bound = ReplaceValue(
            Document,
            brep=None,
            diagnostics=(
                *Document.diagnostics,
                Diagnostic(
                    code="sldprt.width_depth_body_unresolved",
                    message=str(ErrorValue),
                    severity=Severity.WARNING,
                ),
            ),
        )
    return Bound if Settings.include_brep else StripEqGeom(Bound)
