from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# both the folder and its lights use the same resolved list owner and stored tail
def ReadSceneRows(FeatureValue: ArchiveNode) -> tuple[object, ...]:
    ResolvedValue = CastValue(dict[str, object], FeatureValue.FieldsValue["f60"])
    ListValue = CastValue(dict[str, object], ResolvedValue["list"])
    RowsValue = CastValue(list[dict[str, object]], ListValue["items"])
    if ResolvedValue["tail"] != 0 or ListValue["n"] != len(RowsValue):
        raise BodyUnsupported("unsupported SOLIDWORKS scene list state")
    return tuple(RowValue["o"] for RowValue in RowsValue)
