from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.Materials.AttachMatRead import (
    AttachMatRead,
)
from convert.adapters.solidworks.Core.TypedResolved.Materials.CheckMatTree import (
    KMaterialTree,
)
from convert.adapters.solidworks.Core.TypedResolved.Materials.ReadNamedMat import (
    ReadNamedMat,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumDocument import Severity
from interchange.Records.RecordDiagnostic import Diagnostic


# presence of the actual material stream opts in and ordinary unassigned parts keep their projection
def WithPartMat(DocumentValue: CadDocument, ArchiveValue: SldprtArchive) -> CadDocument:
    if ArchiveValue.get(KMaterialTree) is None:
        return DocumentValue
    try:
        Observed = ReadNamedMat(ArchiveValue)
        DocumentValue = AttachMatRead(DocumentValue, Observed)
    except (KeyError, TypeError, ValueError, OverflowError) as ErrorValue:
        DiagnosticValue = Diagnostic(
            code="sldprt.material_assignment_unresolved",
            message=str(ErrorValue),
            severity=Severity.WARNING,
        )
    else:
        DiagnosticValue = Diagnostic(
            code="sldprt.material_domains_unresolved",
            message="The native appearance and complete material catalog properties remain unresolved",
            severity=Severity.INFO,
            attributes=FreezeMapping({"domains": Observed.PendingDomains}),
        )
    return ReplaceValue(
        DocumentValue, diagnostics=(*DocumentValue.diagnostics, DiagnosticValue)
    )
