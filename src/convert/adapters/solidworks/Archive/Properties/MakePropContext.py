from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.NewBodyUsage import NewBodyUsage
from convert.adapters.solidworks.Archive.Properties.ManagerFields import (
    KManagerFields,
    KManagerSchemas,
)


# current property graph readers and writers share the same release and field rules
def MakePropContext(VersionValue: int) -> BodyContext:
    if VersionValue != 19000:
        raise ValueError("part property manager requires archive version 19000")
    return BodyContext(
        VersionValue,
        KManagerFields,
        {},
        KManagerSchemas,
        NewBodyUsage(VersionValue, None),
    )
