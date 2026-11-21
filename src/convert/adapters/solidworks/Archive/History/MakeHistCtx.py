from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.History.HistoryLayouts import (
    KHistoryLayouts,
    KHistorySchemas,
)


# each metadata stream needs its own ordinary version context and independent archive map
def MakeHistCtx(VersionValue: int) -> BodyContext:
    if type(VersionValue) is not int or VersionValue != 19000:
        raise BodyUnsupported("SOLIDWORKS history requires archive version 19000")
    return BodyContext(VersionValue, KHistoryLayouts, {}, KHistorySchemas)
