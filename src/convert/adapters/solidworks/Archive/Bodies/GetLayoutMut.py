from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField


# unsupported schemas must stop before bytes can be mistaken for a complete typed body
def GetLayoutMut(ContextValue: BodyContext, SchemaName: str) -> tuple[NativeField, ...]:
    if ContextValue.VersionValue != 19000:
        raise BodyUnsupported(
            "SOLIDWORKS typed body grammar requires archive version 19000"
        )
    UsageValue = ContextValue.UsageValue
    if SchemaName not in ContextValue.LayoutsValue:
        UsageValue.MissingNames.add(SchemaName)
        raise BodyUnsupported(f"unsupported SOLIDWORKS body schema {SchemaName}")
    UsageValue.SchemaCalls[SchemaName] += 1
    return ContextValue.LayoutsValue[SchemaName]
