from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Definition.Fields.ModelDefLayouts import (
    KModelDefLayouts,
)
from convert.adapters.solidworks.Archive.Definition.Fields.ModelDefSchemas import (
    KModelDefSchemas,
    KOrdDefSchemas,
)
from convert.adapters.solidworks.Archive.Definition.Fields.OrdDefLayouts import (
    KOrdDefLayouts,
)


# model definitions have an independent archive base and admit only the proved version
def ModelDefContext(VersionValue: int, *, OrdinaryOnly: bool = False) -> BodyContext:
    if VersionValue != 19000 or (
        OrdinaryOnly and type(CastValue(object, VersionValue)) is not int
    ):
        raise BodyUnsupported(
            "SOLIDWORKS model Definition requires archive version 19000"
        )
    if OrdinaryOnly:
        return BodyContext(VersionValue, KOrdDefLayouts, {}, KOrdDefSchemas)
    return BodyContext(VersionValue, KModelDefLayouts, {}, KModelDefSchemas)
