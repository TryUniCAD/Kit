from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Definition.Fields.AsmDefLayouts import (
    KAsmDefLayouts,
    KAsmDefSchemas,
)
from convert.adapters.solidworks.Archive.Definition.Fields.ModelDefLayouts import (
    KModelDefLayouts,
)
from convert.adapters.solidworks.Archive.Definition.Fields.ModelDefSchemas import (
    KModelDefSchemas,
)


# model definitions have an independent archive base and admit only the proved version
def ModelDefContext(VersionValue: int, *, Assembly: bool = False) -> BodyContext:
    if type(CastValue(object, VersionValue)) is not int or VersionValue != 19000:
        raise BodyUnsupported(
            "SOLIDWORKS model Definition requires archive version 19000"
        )
    if Assembly:
        return BodyContext(VersionValue, KAsmDefLayouts, {}, KAsmDefSchemas)
    return BodyContext(VersionValue, KModelDefLayouts, {}, KModelDefSchemas)
