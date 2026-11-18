from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.CmgrHeader.ManagerLayouts import (
    KManagerLayouts,
    KManagerSchemas,
)


# lightweight current configuration headers must use their independent ordinary archive rather than legacy list or database modes
def ManagerContext(VersionValue: int) -> BodyContext:
    if type(VersionValue) is not int or VersionValue != 19000:
        raise BodyUnsupported(
            "configuration manager header requires ordinary archive version 19000"
        )
    return BodyContext(VersionValue, KManagerLayouts, {}, KManagerSchemas)
