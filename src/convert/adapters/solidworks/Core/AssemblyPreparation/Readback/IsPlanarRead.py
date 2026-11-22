from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Core.AssemblyPreparation.Readback.IsNestedRead import IsNestedRead
from interchange.document.Models.DocumentModel import CadDocument


# only an ordinary assembly with complete typed mate semantics can enter this inverse
def IsPlanarRead(Document: CadDocument) -> bool:
    ReportValue = Document.metadata.get("solidworks.typed_mates_semantics")
    if not IsNestedRead(Document) or not isinstance(ReportValue, Mapping):
        return False
    Semantics = CastValue(Mapping[str, object], ReportValue)
    return (
        Semantics.get("status") == "admitted"
        and Semantics.get("full_selected_mate_graph") is True
        and Semantics.get("scope") == "ordinary_aligned_mates_direct_part_occurrences"
    )
