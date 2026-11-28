from collections.abc import MutableMapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# explicit escape branches must preserve semantic joins while exercising conditional full index fields
def ExtendLineMut(
    Point: MutableMapping[str, object], LineValue: MutableMapping[str, object]
) -> None:
    Handle = CastValue(ArchiveNode, Point["h1"])
    Handle.FieldsValue["f18"] = Handle.FieldsValue["idx"]
    Handle.FieldsValue["idx"] = 30591
    LineValue["fcc"] = LineValue["fcc_s"]
    LineValue["fcc_s"] = 65535
