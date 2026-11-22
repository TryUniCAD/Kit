from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Bodies.Layouts.BodyLayouts import KBodyLayouts
from convert.adapters.solidworks.Archive.Bodies.Layouts.BodySchemas import KBodySchemas
from convert.adapters.solidworks.Archive.Bodies.Layouts.BodyVirtuals import (
    KBodyVirtuals,
)
from convert.adapters.solidworks.Archive.Bodies.NewBodyUsage import NewBodyUsage


# manager admission retains its distinct registry while sharing ordinary version and evidence guards
def MakeCmgrContext(VersionValue: int, UsageValue: BodyUsage | None) -> BodyContext:
    return BodyContext(
        VersionValue,
        KBodyLayouts,
        KBodyVirtuals,
        KBodySchemas,
        NewBodyUsage(VersionValue, UsageValue),
    )
