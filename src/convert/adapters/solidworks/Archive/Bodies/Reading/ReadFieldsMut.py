from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadFieldMut import ReadFieldMut


# failures need the actual native schema and field path before traversal unwinds
def ReadFieldsMut(FrameValue: ReadFrame, RulesValue: tuple[NativeField, ...]) -> None:
    UsageValue = FrameValue.ContextValue.UsageValue
    for RuleValue in RulesValue:
        UsageValue.FieldCalls[RuleValue.KindValue] += 1
        UsageValue.FieldPath.append(RuleValue.NameValue or RuleValue.KindValue)
        try:
            ReadFieldMut(FrameValue, RuleValue)
        except BodyUnsupported:
            raise
        except (TypeError, ValueError, KeyError) as ErrorInfo:
            SchemaPath = "/".join(UsageValue.SchemaPath)
            FieldPath = "/".join(UsageValue.FieldPath)
            Offset = FrameValue.ReaderValue.Cursor.OffsetValue
            raise ValueError(
                f"SOLIDWORKS body {SchemaPath} field {FieldPath} at {Offset}: {ErrorInfo}"
            ) from ErrorInfo
        finally:
            _ = UsageValue.FieldPath.pop()
