from typing import Mapping as TypeMap

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.Offsets.FaceOffset import FaceOffset


# filtered offset views record intentional geometry omission only after their complete graph validates
def FilterMetadata(Document: CadDocument, IncludeBrep: bool) -> TypeMap[str, object]:
    if (
        not IncludeBrep
        and Document.brep is not None
        and any(
            isinstance(Feature.definition, FaceOffset)
            for Feature in Document.feature_timeline
        )
    ):
        Document.assert_valid()
        return {**Document.metadata, "kit.omitted_brep": True}
    return Document.metadata
