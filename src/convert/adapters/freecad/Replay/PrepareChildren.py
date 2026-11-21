from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace as Replace

from convert.adapters.freecad.Replay.MappedOuter import MappedOuter
from interchange.document.Models.DocumentModel import CadDocument


# a carried child can verify its own archive even when the parent lacks its linked source
def PrepareChildren(
    DocValue: CadDocument, PrepareModel: Callable[[CadDocument], CadDocument]
) -> CadDocument:
    Metadata = MappedOuter(DocValue.metadata, PrepareModel)
    Assembly = DocValue.assembly
    if Assembly is not None:
        Assembly = Replace(
            Assembly,
            documents=tuple(
                Replace(ItemValue, document=PrepareModel(ItemValue.document))
                for ItemValue in Assembly.documents
            ),
        )
    return Replace(DocValue, metadata=Metadata, assembly=Assembly)
