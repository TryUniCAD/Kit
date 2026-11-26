from convert.adapters.solidworks.Archive.Bodies.GetLayoutMut import GetLayoutMut
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame


# inherited schemas retain their real owner while contributing independently tracked field rules
def ReadSchemaMut(FrameValue: ReadFrame, SchemaName: str) -> None:
    RulesValue = GetLayoutMut(FrameValue.ContextValue, SchemaName)
    SchemaPath = FrameValue.ContextValue.UsageValue.SchemaPath
    SchemaPath.append(SchemaName)
    try:
        FrameValue.FieldsReader(FrameValue, RulesValue)
    finally:
        _ = SchemaPath.pop()
