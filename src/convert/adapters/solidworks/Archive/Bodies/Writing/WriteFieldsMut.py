from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from struct import error as StructError

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteFieldMut import (
    WriteFieldMut,
)


# malformed model fields must produce a bounded schema diagnostic instead of partial successful output
def WriteFieldsMut(FrameValue: WriteFrame, RulesValue: tuple[NativeField, ...]) -> None:
    UsageValue = FrameValue.WriterValue.ContextValue.UsageValue
    for RuleValue in RulesValue:
        UsageValue.FieldCalls[RuleValue.KindValue] += 1
        UsageValue.FieldPath.append(RuleValue.NameValue or RuleValue.KindValue)
        try:
            WriteFieldMut(FrameValue, RuleValue)
        except BodyUnsupported:
            raise
        except (TypeError, ValueError, KeyError, StructError) as ErrorInfo:
            SchemaPath = "/".join(UsageValue.SchemaPath)
            FieldPath = "/".join(UsageValue.FieldPath)
            Offset = len(FrameValue.WriterValue.OutputValue)
            raise ValueError(
                f"SOLIDWORKS body {SchemaPath} field {FieldPath} at {Offset}: {ErrorInfo}"
            ) from ErrorInfo
        finally:
            _ = UsageValue.FieldPath.pop()
