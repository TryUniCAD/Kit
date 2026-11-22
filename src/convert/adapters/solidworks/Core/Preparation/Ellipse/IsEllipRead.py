from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.NativeSourceKey import KSourceFormatKey
from interchange.document.Models.DocumentModel import CadDocument


# only the actual typed cold ellipse diagnostic may enter complete regenerated source comparison
def IsEllipRead(Document: CadDocument) -> bool:
    Report = Document.metadata.get("solidworks.typed_resolved_semantics")
    if not isinstance(Report, Mapping):
        return False
    ReportValue = CastValue(Mapping[str, object], Report)
    return (
        Document.assembly is None
        and Document.DrawingValue is None
        and Document.source.format_id == KPartFormatId
        and Document.source.container_version == "4"
        and Document.metadata.get(KSourceFormatKey) == KPartFormatId
        and ReportValue.get("status") == "supplemented_cold_full_ellipse"
        and ReportValue.get("typed_geometry_projection") is True
        and not Document.brep_payloads
    )
