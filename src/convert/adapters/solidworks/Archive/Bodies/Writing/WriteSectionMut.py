from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# section lengths must derive from actual emitted fields after their graph dependencies are known
def WriteSectionMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    Buffer = FrameValue.WriterValue.OutputValue
    StartValue = len(Buffer)
    Buffer.extend(EncodeScalar(0, "u32"))
    FrameValue.FieldsWriter(FrameValue, RuleValue.BodyValue)
    Buffer[StartValue : StartValue + 4] = EncodeScalar(
        len(Buffer) - StartValue - 4, "u32"
    )
