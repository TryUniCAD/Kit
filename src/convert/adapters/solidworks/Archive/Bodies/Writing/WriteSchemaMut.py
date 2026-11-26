from convert.adapters.solidworks.Archive.Bodies.GetLayoutMut import GetLayoutMut
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame


# emitted bodies follow the same inherited field order without retaining recorded byte operations
def WriteSchemaMut(FrameValue: WriteFrame, SchemaName: str) -> None:
    ContextValue = FrameValue.WriterValue.ContextValue
    RulesValue = GetLayoutMut(ContextValue, SchemaName)
    SchemaPath = ContextValue.UsageValue.SchemaPath
    SchemaPath.append(SchemaName)
    try:
        FrameValue.FieldsWriter(FrameValue, RulesValue)
    finally:
        _ = SchemaPath.pop()
