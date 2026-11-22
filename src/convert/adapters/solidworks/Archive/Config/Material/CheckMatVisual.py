from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# archive inspection only admits the distinct currently measured material selectors
def CheckMatVisual(VisualValue: ArchiveNode) -> None:
    FieldsValue = VisualValue.FieldsValue
    MaterialValue = CastValue(Mapping[str, object], FieldsValue["f20"])
    ModeValue = (MaterialValue["f70"], MaterialValue["has80"])
    if (
        ModeValue not in ((0, 0), (0, 1), (1, 0))
        or MaterialValue["has90"] != 1
        or FieldsValue["has88"] != 1
    ):
        raise BodyUnsupported("unsupported SOLIDWORKS part material visual selectors")
