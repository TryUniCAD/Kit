from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Bodies.Layouts.BodyLayouts import KBodyLayouts
from convert.adapters.solidworks.Archive.Bodies.Layouts.BodySchemas import KBodySchemas
from convert.adapters.solidworks.Archive.Bodies.Layouts.BodyVirtuals import (
    KBodyVirtuals,
)


# manager admission must isolate usage and exclude unproved document versions before reading fields
def MakeCmgrContext(VersionValue: int, UsageValue: BodyUsage | None) -> BodyContext:
    if type(VersionValue) is not int or VersionValue != 19000:
        raise BodyUnsupported(
            f"unsupported SOLIDWORKS manager archive version {VersionValue}"
        )
    if UsageValue is None:
        UsageValue = BodyUsage()
    if (
        UsageValue.IsComplete
        or UsageValue.SchemaCalls
        or UsageValue.FieldCalls
        or UsageValue.SchemaPath
        or UsageValue.FieldPath
        or UsageValue.MissingNames
    ):
        raise ValueError("SOLIDWORKS manager requires a fresh usage context")
    return BodyContext(
        VersionValue, KBodyLayouts, KBodyVirtuals, KBodySchemas, UsageValue
    )
