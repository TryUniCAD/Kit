from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.PartMatFields import (
    KPartMatFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.FeatureFields import (
    KFeatureFields,
)
from convert.adapters.solidworks.Archive.Config.Material.MatTypes import KPartMatSchemas
from convert.adapters.solidworks.Archive.Header.HeaderFields import KHeaderVersion

# density uses the shared lightweight node order before its own scalar fields
KMatLayouts = MappingProxyType({**KFeatureFields, **KPartMatFields})


# density archive conditions determine whether its override flag can even exist
def MakeMatCtx(VersionValue: int, ConditionBits: int) -> BodyContext:
    if type(VersionValue) is not int or VersionValue != KHeaderVersion:
        raise BodyUnsupported("SOLIDWORKS part material requires archive version 19000")
    if type(ConditionBits) is not int or ConditionBits != 0:
        raise BodyUnsupported("unsupported SOLIDWORKS part material archive conditions")
    return BodyContext(VersionValue, KMatLayouts, {}, KPartMatSchemas)
