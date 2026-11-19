from convert.adapters.solidworks.Archive.Construction.Views.MakeViewNode import (
    MakeViewNode,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# a drawing constructor indexes ten identity views and uses its own full sheet name followed by unused slots
def MakeDrawViews(LanguageId: int) -> tuple[ArchiveNode, ...]:
    if LanguageId != 1033:
        raise ValueError("drawing standard view vocabulary requires English resources")
    return (
        MakeViewNode("*Full Sheet", 0, None),
        *(MakeViewNode("Unused", IndexValue, None) for IndexValue in range(1, 10)),
    )
