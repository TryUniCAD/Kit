from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.History.HistoryLayouts import (
    KHistoryLayouts,
    KHistorySchemas,
)


# current ordinary history has an independent map and cannot reuse flat database or early version grammar without its native branches
def HistoryContext(VersionValue: int) -> BodyContext:
    if type(VersionValue) is not int or VersionValue != 19000:
        raise BodyUnsupported(
            "history construction codec requires ordinary version 19000"
        )
    return BodyContext(VersionValue, KHistoryLayouts, {}, KHistorySchemas)
